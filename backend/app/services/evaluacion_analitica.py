"""Verificación de lectura, independiente del cálculo de entrenamiento (variables v1).

No llama a calcular, particionar, Contexto.fit ni Contexto.transformar. Reconstruye
las referencias del corte y contrasta resultados publicados. La reproducción del
estimador privado se ofrece únicamente a la CLI, nunca deserializa desde HTTP.
"""

import hashlib
import io
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from uuid import UUID

import numpy as np

from app.services.datos_analitica import huella

PARTES = ("entrenamiento", "calibracion", "evaluacion")
CONTENIDO = (
    "articulo_id",
    "fecha",
    "detalle",
    "referencia",
    "area",
    "ingresos",
    "salidas",
    "saldo_registrado",
)


def _datos(f):
    return (
        (f["ingresos"] or 0) + (f["salidas"] or 0),
        "ingreso" if (f["ingresos"] or 0) > 0 else "salida",
    )


def reconstruir(filas, entrenamiento):
    """Estadísticas por mediana/MAD y frecuencias, sin utilizar el preprocesador guardado."""
    cantidades, globales = defaultdict(list), defaultdict(list)
    nodos, pares, totales = Counter(), Counter(), Counter()
    for f in entrenamiento:
        cantidad, direccion = _datos(f)
        clave, nodo = (f["articulo_id"], direccion), f["nodo_grafo"]
        cantidades[clave].append(cantidad)
        globales[direccion].append(cantidad)
        nodos[nodo] += 1
        pares[(clave, nodo)] += 1
        totales[clave] += 1

    def stats(valores):
        m = float(median(valores))
        return m, max(1.0, float(median(abs(v - m) for v in valores)))

    estadisticas = {k: stats(v) for k, v in cantidades.items()}
    respaldo = {k: stats(v) for k, v in globales.items()}
    matriz, contextos = [], []
    for f in filas:
        cantidad, direccion = _datos(f)
        clave, nodo = (f["articulo_id"], direccion), f["nodo_grafo"]
        n = totales[clave]
        m, mad = estadisticas.get(clave, respaldo.get(direccion, (1.0, 1.0)))
        fn = (nodos[nodo] + 1) / (len(entrenamiento) + len(nodos) + 1)
        fp = (pares[(clave, nodo)] + 1) / (n + len(nodos) + 1)
        ausente = not nodo or nodo in ("Origen no especificado", "Destino no especificado")
        matriz.append(
            [
                math.log1p(cantidad),
                math.log((cantidad + 1) / (m + 1)),
                math.log1p(abs(cantidad - m) / mad),
                -math.log(fn),
                -math.log(fp),
                int(ausente),
                int(direccion == "salida"),
            ]
        )
        contextos.append(
            dict(
                cantidad=cantidad,
                direccion=direccion,
                mediana=m,
                referencias=n,
                frecuencia_nodo=fn,
                regla_magnitud=bool(n and cantidad > m * 3),
                score_regla=float(cantidad / max(m, 1)) if n else 0.0,
            )
        )
    referencias = dict(
        cantidades=dict(cantidades),
        globales=dict(globales),
        nodos=nodos,
        pares=pares,
        totales=totales,
        total=len(entrenamiento),
        estadisticas=estadisticas,
        respaldo=respaldo,
    )
    return np.asarray(matriz), contextos, referencias


def _igual(a, b):
    if isinstance(b, float | int) and not isinstance(b, bool):
        return (
            isinstance(a, float | int)
            and math.isfinite(a)
            and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
        )
    return a == b


def _control(filas, por_id, semilla):
    # Mantiene el orden del corte, anterior al barajado reproducible.
    ids = [
        f["id"]
        for f in filas
        if f["id"] in por_id
        and por_id[f["id"]].particion == "evaluacion"
        and not por_id[f["id"]].alerta
    ]
    np.random.default_rng(semilla).shuffle(ids)
    return ids[:20]


def _asignacion(filas, semilla):
    """Reconstruye el sorteo v1 desde contenido y lotes, sin leer las etiquetas guardadas."""
    padres = {f["lote_id"]: f["lote_id"] for f in filas}
    if None in padres or not padres:
        return {}

    def raiz(lote):
        while padres[lote] != lote:
            lote = padres[lote]
        return lote

    primero = {}
    for f in filas:
        firma = huella({k: f[k] for k in CONTENIDO})
        previo = primero.setdefault(firma, f["lote_id"])
        padres[raiz(f["lote_id"])] = raiz(previo)
    grupos = sorted({raiz(lote) for lote in padres})
    np.random.default_rng(semilla).shuffle(grupos)
    n = max(1, len(grupos) // 5)
    particiones = {
        g: "calibracion" if i < n else "evaluacion" if i < 2 * n else "entrenamiento"
        for i, g in enumerate(grupos)
    }
    return {f["id"]: particiones[raiz(f["lote_id"])] for f in filas}


def progreso(ids, por_id, integra=True):
    """Denominador congelado: una fila faltante o un error nunca reduce k."""
    rs = [
        por_id[i] for i in dict.fromkeys(ids) if i in por_id and por_id[i].particion == "evaluacion"
    ]
    concluyentes = [
        r
        for r in rs
        if r.estado_revision in ("JUSTIFICADO", "CERRADO")
        and r.etiqueta in ("LEGITIMO", "INUSUAL_RELEVANTE")
    ]
    relevantes = sum(r.etiqueta == "INUSUAL_RELEVANTE" for r in concluyentes)
    duplicados = len(ids) - len(set(ids))
    integra = integra and not duplicados and len(rs) == len(ids)
    return dict(
        k=len(ids),
        disponibles=len(rs),
        sin_resultado=len(ids) - duplicados - len(rs),
        ids_duplicados=duplicados,
        seleccion_integra=integra,
        revisados_concluyentes=len(concluyentes),
        relevantes=relevantes,
        pendientes=len(ids) - len(concluyentes),
        errores_documentales=sum(r.etiqueta == "ERROR_DOCUMENTAL" for r in rs),
        no_concluyentes=sum(r.etiqueta == "NO_CONCLUYENTE" for r in rs),
        precision_at_k=(
            relevantes / len(ids) if integra and ids and len(concluyentes) == len(ids) else None
        ),
    )


def diagnosticar(modelo, resultados):
    """Comprueba integridad y separación sin modificar datos, modelo ni revisiones."""
    checks = []

    def check(codigo, titulo, ok, detalle, incidencias=()):
        checks.append(
            dict(
                codigo=codigo,
                titulo=titulo,
                estado="OK" if ok else "FALLO",
                detalle=detalle,
                ejemplos=list(incidencias)[:10],
            )
        )

    corte, metricas = modelo.corte, modelo.metricas or {}
    excluidos_lista = [i for ids in corte["exclusiones"].values() for i in ids]
    excluidos = set(excluidos_lista)
    filas = [f for f in corte["filas"] if f["id"] not in excluidos]
    ids = [f["id"] for f in filas]
    por_id = {r.movimiento_id: r for r in resultados}
    check(
        "huella",
        "Huella del corte",
        huella(corte["filas"]) == modelo.huella,
        "Comparación con el SHA-256 de la fotografía conservada.",
    )
    ids_corte = {f["id"] for f in corte["filas"]}
    seleccion_ok = (
        len(ids) == len(set(ids)) == corte["perfil"]["elegibles"]
        and len(ids_corte) == len(corte["filas"])
        and len(excluidos_lista) == len(excluidos)
        and excluidos <= ids_corte
        and len(ids) + len(excluidos) == len(corte["filas"])
    )
    check(
        "seleccion",
        "Selección congelada",
        seleccion_ok,
        f"{len(ids)} candidatos; {len(excluidos)} exclusiones conservadas.",
    )
    faltantes, extras = set(ids) - set(por_id), set(por_id) - set(ids)
    cobertura_ok = not faltantes and not extras and len(resultados) == len(por_id)
    check(
        "resultados",
        "Resultados completos",
        cobertura_ok,
        f"{len(faltantes)} faltantes; {len(extras)} ajenos al corte.",
        sorted(faltantes | extras),
    )
    distintos = [
        f["id"]
        for f in filas
        if f["id"] in por_id
        and (
            por_id[f["id"]].snapshot != f
            or por_id[f["id"]].articulo_id != f["articulo_id"]
            or por_id[f["id"]].gestion != int(f["fecha"][:4])
            or por_id[f["id"]].nodo != f["nodo_grafo"]
        )
    ]
    check(
        "snapshots",
        "Procedencia de los resultados",
        not distintos,
        f"{len(distintos)} resultados difieren de la fila o sus índices congelados.",
        distintos,
    )
    partes = Counter(r.particion for r in resultados)
    check(
        "particiones",
        "Conteos de particiones",
        all(p in PARTES for p in partes)
        and {p: partes[p] for p in PARTES} == metricas.get("particiones"),
        ", ".join(f"{p}: {partes[p]}" for p in PARTES),
    )
    lotes, contenidos = defaultdict(set), defaultdict(set)
    for f in filas:
        if f["id"] in por_id:
            parte = por_id[f["id"]].particion
            lotes[f["lote_id"]].add(parte)
            contenidos[huella({k: f[k] for k in CONTENIDO})].add(parte)
    fugas_lote = [lote for lote, ps in lotes.items() if len(ps) > 1 or lote is None]
    fugas_contenido = sum(len(ps) > 1 for ps in contenidos.values())
    check(
        "separacion",
        "Lotes y duplicados separados",
        not fugas_lote and not fugas_contenido,
        f"{len(fugas_lote)} lotes y {fugas_contenido} contenidos cruzan particiones.",
        fugas_lote,
    )
    if modelo.configuracion.get("modo") == "TEMPORAL":
        cal = modelo.configuracion["gestion_evaluacion"] - 1
        asignacion = {f["id"]: (
            "entrenamiento" if int(f["fecha"][:4]) < cal else
            "calibracion" if int(f["fecha"][:4]) == cal else
            "evaluacion" if int(f["fecha"][:4]) == cal + 1 else "fuera_de_periodo"
        ) for f in filas}
    else:
        asignacion = _asignacion(filas, modelo.configuracion["semilla"])
    cambiados = [i for i in ids if i in por_id and por_id[i].particion != asignacion.get(i)]
    check(
        "asignacion",
        "Asignación reproducible de particiones",
        not cambiados,
        f"{len(cambiados)} filas difieren de la estrategia y períodos conservados.",
        cambiados,
    )
    train = [f for f in filas if f["id"] in por_id and por_id[f["id"]].particion == "entrenamiento"]
    _, contextos, _ = reconstruir(filas, train)
    contextos = dict(zip(ids, contextos))
    diferentes = [
        i
        for i in ids
        if i in por_id
        and any(not _igual(por_id[i].contexto.get(k), v) for k, v in contextos[i].items())
    ]
    check(
        "referencias",
        "Referencias solo de entrenamiento",
        not diferentes,
        f"{len(diferentes)} contextos no coinciden con la reconstrucción independiente.",
        diferentes,
    )
    evaluacion = [por_id[i] for i in ids if i in por_id and por_id[i].particion == "evaluacion"]
    cal = [r.score for r in resultados if r.particion == "calibracion"]
    finitos = (
        all(math.isfinite(r.score) for r in resultados)
        and modelo.umbral is not None
        and math.isfinite(modelo.umbral)
    )
    esperado = (
        float(np.quantile(cal, 1 - modelo.configuracion["porcentaje_revision"] / 100))
        if cal and finitos
        else None
    )
    mal_alerta = [
        r.movimiento_id for r in resultados if finitos and r.alerta != (r.score > modelo.umbral)
    ]
    umbral_ok = (
        esperado is not None
        and _igual(modelo.umbral, esperado)
        and not mal_alerta
        and sum(r.alerta for r in resultados) == metricas.get("alertas")
    )
    check(
        "calibracion",
        "Umbral y alertas de calibración",
        umbral_ok,
        f"Umbral reconstruido: {esperado}; {len(mal_alerta)} indicadores incompatibles.",
        mal_alerta,
    )
    k = min(20, len(evaluacion))
    top = [
        r.movimiento_id for r in sorted(evaluacion, key=lambda r: (-r.score, r.movimiento_id))[:k]
    ]
    regla = [
        r.movimiento_id
        for r in sorted(
            evaluacion, key=lambda r: (-contextos[r.movimiento_id]["score_regla"], r.movimiento_id)
        )[:k]
    ]
    control = _control(filas, por_id, modelo.configuracion["semilla"])
    controles_guardados = {r.movimiento_id for r in resultados if r.muestra_control}
    listas_ok = (
        k == metricas.get("k")
        and top == metricas.get("top_evaluacion")
        and regla == metricas.get("top_regla")
        and set(control) == controles_guardados
        and len(control) == metricas.get("muestra_control")
    )
    check(
        "muestras",
        "Selecciones y control reproducibles",
        listas_ok,
        f"Top modelo: {k}; regla: {k}; control: {len(control)}. Orden y pertenencia verificados.",
    )
    sin_ref = sum(contextos[r.movimiento_id]["referencias"] == 0 for r in evaluacion)
    check(
        "cobertura",
        "Conteo de referencias propias",
        sin_ref == metricas.get("sin_referencia_propia_evaluacion"),
        f"{sin_ref}/{len(evaluacion)} sin referencia propia.",
    )
    estado = (
        "NO_VERIFICADO"
        if modelo.estado != "COMPLETADO"
        else ("CONSISTENTE" if all(c["estado"] == "OK" for c in checks) else "INCONSISTENTE")
    )
    integra = estado == "CONSISTENTE"
    progreso_humano = {
        "modelo": progreso(metricas.get("top_evaluacion", []), por_id, integra),
        "regla": progreso(metricas.get("top_regla", []), por_id, integra),
        "control": progreso(control, por_id, integra),
        "advertencia": "Revisa las selecciones completas. Los errores documentales y casos "
        "no concluyentes siguen pendientes. No estima recall ni fraude.",
    }
    return dict(
        version=1,
        modelo_id=modelo.id,
        estado=estado,
        comprobaciones=checks,
        reproduccion_artefacto="NO_VERIFICADO",
        evaluacion=progreso_humano,
        cobertura=dict(
            evaluados=len(resultados),
            particiones={p: partes[p] for p in PARTES},
            evaluacion=len(evaluacion),
            sin_referencia_propia=sin_ref,
            porcentaje_sin_referencia=100 * sin_ref / len(evaluacion) if evaluacion else None,
            regla_sin_referencia_top=sum(contextos[i]["referencias"] == 0 for i in regla),
        ),
        advertencia="La consistencia técnica no demuestra utilidad ni precisión. "
        "La reproducción del archivo privado se verifica con la herramienta local.",
    )


def reproducir_artefacto(modelo, resultados, directorio):
    """CLI local: hash antes de cargar el mismo contenido, y score sin fit/reentrenamiento."""
    import joblib
    import sklearn

    checks = []

    def check(codigo, titulo, ok, detalle):
        checks.append(
            dict(
                codigo=codigo,
                titulo=titulo,
                estado="OK" if ok else "FALLO",
                detalle=detalle,
                ejemplos=[],
            )
        )

    try:
        id_valido = str(UUID(modelo.id)) == modelo.id
    except (ValueError, AttributeError):
        id_valido = False
    carpeta = Path(directorio).resolve()
    ruta = carpeta / (modelo.id + ".joblib") if id_valido else None
    seguro = (
        id_valido and ruta.is_file() and not ruta.is_symlink() and ruta.resolve().parent == carpeta
    )
    check("archivo", "Archivo privado del modelo", seguro, "UUID y ubicación privada comprobados.")
    if not seguro:
        return dict(estado="INCONSISTENTE", comprobaciones=checks)
    contenido = ruta.read_bytes()
    digest = hashlib.sha256(contenido).hexdigest()
    integro = (
        bool(re.fullmatch(r"[0-9a-f]{64}", modelo.artefacto_sha256 or ""))
        and digest == modelo.artefacto_sha256
    )
    check("sha256", "SHA-256 del artefacto", integro, "Hash comprobado antes de deserializar.")
    if not integro:
        return dict(estado="INCONSISTENTE", comprobaciones=checks)
    versiones = dict(
        python=sys.version.split()[0], scikit_learn=sklearn.__version__, numpy=np.__version__
    )
    compatibles = versiones == (modelo.metricas or {}).get("dependencias")
    check("dependencias", "Versiones del entorno", compatibles, str(versiones))
    if not compatibles:
        return dict(estado="NO_VERIFICADO", comprobaciones=checks)
    artefacto = joblib.load(io.BytesIO(contenido))
    metadatos_ok = all(
        artefacto.get(k) == v
        for k, v in dict(
            corte=modelo.corte,
            configuracion=modelo.configuracion,
            metricas=modelo.metricas,
            umbral=modelo.umbral,
        ).items()
    )
    check(
        "metadatos",
        "Metadatos del artefacto",
        metadatos_ok,
        "Corte, configuración, métricas y umbral.",
    )
    if not metadatos_ok or (modelo.metricas or {}).get("version_variables") != 1:
        return dict(estado="INCONSISTENTE", comprobaciones=checks)
    por_id = {r.movimiento_id: r for r in resultados}
    excluidos = {i for ids in modelo.corte["exclusiones"].values() for i in ids}
    filas = [f for f in modelo.corte["filas"] if f["id"] not in excluidos]
    if set(por_id) != {f["id"] for f in filas}:
        check(
            "replay",
            "Reproducción de puntuaciones",
            False,
            "Faltan resultados completos para comparar.",
        )
        return dict(estado="INCONSISTENTE", comprobaciones=checks)
    entrenamiento = [f for f in filas if por_id[f["id"]].particion == "entrenamiento"]
    matriz, _, referencias = reconstruir(filas, entrenamiento)
    contexto = artefacto["contexto"]
    check(
        "preprocesador",
        "Preprocesador conservado",
        all(getattr(contexto, k, None) == v for k, v in referencias.items()),
        "Estadísticas y frecuencias contrastadas con entrenamiento exclusivamente.",
    )
    parametros = artefacto["modelo"].get_params()
    parametros_ok = (
        all(
            parametros.get(k) == v
            for k, v in dict(
                n_estimators=modelo.configuracion["arboles"],
                max_samples=min(256, len(entrenamiento)),
                random_state=modelo.configuracion["semilla"],
                contamination="auto",
                n_jobs=1,
            ).items()
        )
        and artefacto["modelo"].n_features_in_ == 7
        and artefacto["modelo"]._n_samples == len(entrenamiento)
        and len(artefacto["modelo"].estimators_) == modelo.configuracion["arboles"]
        and artefacto["modelo"].max_samples_ == min(256, len(entrenamiento))
    )
    check(
        "parametros",
        "Parámetros del estimador",
        parametros_ok,
        "Árboles, semilla, muestras y siete variables.",
    )
    scores = -artefacto["modelo"].score_samples(matriz)
    errores = [
        f["id"]
        for f, score in zip(filas, scores)
        if not _igual(por_id[f["id"]].score, float(score))
    ]
    max_error = max(abs(float(score) - por_id[f["id"]].score) for f, score in zip(filas, scores))
    check(
        "replay",
        "Reproducción de puntuaciones",
        not errores,
        f"{len(filas)} puntuaciones; {len(errores)} discrepancias; "
        f"error máximo {max_error:.3g}. Sin fit.",
    )
    fuentes = artefacto.get("fuentes", {})
    fuentes_ok = set(fuentes) == {
        "trabajador_analitica.py",
        "isolation_historico.py",
        "datos_analitica.py",
    } and all(isinstance(v, str) and v.strip() for v in fuentes.values())
    cambiadas = [
        nombre
        for nombre, texto in fuentes.items()
        if nombre in ("trabajador_analitica.py", "isolation_historico.py", "datos_analitica.py")
        if not Path(__file__).with_name(nombre).is_file()
        or Path(__file__).with_name(nombre).read_text(encoding="utf-8-sig") != texto
    ]
    check(
        "fuentes",
        "Fuentes conservadas",
        fuentes_ok,
        (
            "Sin diferencias."
            if not cambiadas
            else "El código actual tiene cambios posteriores en "
            + ", ".join(cambiadas)
            + ". Se conservan las fuentes originales; ver comprobación de puntuaciones."
        ),
    )
    if fuentes_ok and cambiadas:
        checks[-1]["estado"] = "ADVERTENCIA"
    return dict(
        estado=(
            "CONSISTENTE" if not any(c["estado"] == "FALLO" for c in checks) else "INCONSISTENTE"
        ),
        comprobaciones=checks,
        sha256=digest,
    )
