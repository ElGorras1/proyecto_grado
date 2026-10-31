"""Estudios congelados y etiquetas nuevas; no reutiliza decisiones HIL ni entrena."""

from collections import Counter
from hashlib import sha256
from math import ceil
from random import Random

from fastapi import HTTPException

from app.models.activos import Activo
from app.models.auditoria import AuditoriaSistema
from app.models.auditoria_historica import ModeloHistorico, ResultadoHistorico
from app.models.kardex import MovimientoKardex
from app.services.cierre_documental import foto_huella
from app.services.datos_analitica import huella, snapshot
from app.services.evaluacion_analitica import diagnosticar

CREAR = "crear_estudio_validacion"
ETIQUETAR = "etiquetar_estudio_validacion"
RECURSO = "estudio_validacion"
CONCLUSIVAS = {
    "DOCUMENTAL": {"COINCIDE_DOCUMENTO", "DIFERENCIA_DOCUMENTO"},
    "DETECTOR": {"LEGITIMO", "INUSUAL_RELEVANTE"},
}
CONCLUSIVAS_V2 = {"DOCUMENTAL": CONCLUSIVAS["DOCUMENTAL"], "DETECTOR": {"NORMAL", "ANOMALO"}}
METODO_V2 = "aleatorio_simple_sin_reemplazo_v2"
CRITERIOS = {
    "NORMAL": "Respaldo suficiente y sin desviación verificada de los criterios institucionales.",
    "ANOMALO": "Inconsistencia verificada en cantidades, fechas, tipo de operación o áreas respecto de documentos.",
    "INDETERMINADO": "Respaldo insuficiente para decidir; requiere segunda revisión antes de excluirlo del cálculo principal.",
}
CAMPOS = (
    "id",
    "articulo_id",
    "articulo",
    "codigo",
    "lote_id",
    "numero_pagina",
    "orden_fila",
    "fecha",
    "fecha_documental_texto",
    "fecha_precision",
    "detalle",
    "referencia",
    "area",
    "ingresos",
    "salidas",
    "saldo_registrado",
    "ruta_imagen_respaldo",
)
ALCANCE = (
    "Resultados del corte y la muestra seleccionada, sin extrapolación al archivo completo. "
    "La concordancia de transcripción vigente no mide CER/WER del OCR original. "
    "Inusual relevante no significa fraude. No se reajusta el umbral con evaluación reservada."
)
ALCANCE_V2 = (
    "Evaluación conforme al protocolo del capítulo I: normal, anómalo e indeterminado. "
    "Una anomalía exige inconsistencia documental verificada y no acredita fraude. "
    "Los indeterminados persistentes tras segunda revisión se informan fuera del denominador principal. "
    "El marco técnico requiere confirmación institucional. La concordancia vigente no mide exactitud del OCR original. "
    "El umbral permanece fijado antes de las etiquetas; no se extrapolan métricas al archivo completo."
)


def conclusivas(datos):
    return (CONCLUSIVAS_V2 if datos.get("version", 1) >= 2 else CONCLUSIVAS)[datos["tipo"]]


def indeterminada(datos):
    return (
        "INDETERMINADO"
        if datos.get("version", 1) >= 2 and datos["tipo"] == "DETECTOR"
        else "NO_CONCLUYENTE"
    )


def tamano_documental(n):
    """Recomendación para proporciones: Z=1,96, p=q=0,5 y e=0,05; no fija el test de IA."""
    return ceil(n * 1.96**2 * 0.25 / ((n - 1) * 0.05**2 + 1.96**2 * 0.25)) if n else 0


def seleccionar(ids, tamano, semilla, version=1):
    """Sorteo por huella de semilla/ID, sin consultar etiquetas ni puntuaciones."""
    if version >= 2:
        poblacion = sorted(set(ids))
        return Random(semilla).sample(poblacion, min(tamano, len(poblacion)))
    return sorted(set(ids), key=lambda i: (sha256(f"{semilla}:{i}".encode()).digest(), i))[:tamano]


def obtener_poblacion(db, tipo, modelo_id):
    modelo = None
    if tipo == "DETECTOR":
        modelo = db.get(ModeloHistorico, modelo_id)
        if modelo is None:
            raise HTTPException(404, "Modelo no encontrado")
        resultados = db.query(ResultadoHistorico).filter_by(modelo_id=modelo.id).all()
        if diagnosticar(modelo, resultados)["estado"] != "CONSISTENTE":
            raise HTTPException(
                409, "El modelo y su corte deben estar completos y ser consistentes."
            )
        poblacion = {f.movimiento_id: f for f in resultados if f.particion == "evaluacion"}
    else:
        poblacion = {
            m.id: (m, a)
            for m, a in db.query(MovimientoKardex, Activo)
            .join(Activo, Activo.id == MovimientoKardex.articulo_id)
            .filter(
                MovimientoKardex.lote_id.isnot(None),
                MovimientoKardex.estado == "ACTIVO",
                MovimientoKardex.ruta_imagen_respaldo.isnot(None),
                MovimientoKardex.ruta_imagen_respaldo != "",
            )
        }
    if not poblacion:
        raise HTTPException(409, "No hay filas disponibles en la población de este estudio.")
    return modelo, poblacion


def marco(db, tipo, modelo_id=None):
    _, poblacion = obtener_poblacion(db, tipo, modelo_id)
    return dict(
        poblacion=len(poblacion),
        poblacion_huella=huella(sorted(poblacion)),
        unidad="MOVIMIENTO",
        confirmacion_institucional="PENDIENTE",
        tamano_documental_sugerido=(
            tamano_documental(len(poblacion)) if tipo == "DOCUMENTAL" else None
        ),
        parametros_documentales=dict(z=1.96, p=0.5, q=0.5, error=0.05),
        filtros=(
            "Históricos activos con ruta de fotografía; legibilidad y autorización por confirmar."
            if tipo == "DOCUMENTAL"
            else "Solo evaluación reservada de la versión consistente; no se sobremuestrean alertas."
        ),
    )


def crear_datos(db, tipo, modelo_id, tamano, semilla, referencia_protocolo):
    modelo, poblacion = obtener_poblacion(db, tipo, modelo_id)
    if tamano > len(poblacion):
        raise HTTPException(
            422,
            f"Se solicitaron {tamano} filas y el marco contiene {len(poblacion)}. Ajusta el tamaño antes de crear el estudio.",
        )
    ids = seleccionar(poblacion, tamano, semilla, version=2)
    fotos, items = {}, []
    for mid in ids:
        origen = poblacion[mid].snapshot if modelo else snapshot(*poblacion[mid])
        dato = {k: origen.get(k) for k in CAMPOS}
        ruta = dato["ruta_imagen_respaldo"]
        if ruta not in fotos:
            fotos[ruta] = foto_huella(ruta)
        item = dict(id=mid, documento=dato, foto_sha256=fotos[ruta])
        if modelo:
            item["prediccion"] = poblacion[mid].alerta
        items.append(item)
    datos = dict(
        version=2,
        tipo=tipo,
        semilla=semilla,
        referencia_protocolo=referencia_protocolo,
        metodo=METODO_V2,
        tamano_solicitado=tamano,
        poblacion_ids=sorted(poblacion),
        items=items,
        modelo_id=modelo.id if modelo else None,
        modelo_huella=modelo.huella if modelo else None,
        entrenador_id=modelo.usuario_id if modelo else None,
        umbral=modelo.umbral if modelo else None,
        alcance=ALCANCE_V2,
        publicacion_institucional="PENDIENTE",
        criterios_referencia=CRITERIOS if tipo == "DETECTOR" else {},
        diseno_muestral=dict(
            unidad="MOVIMIENTO",
            sin_reemplazo=True,
            poblacion=len(poblacion),
            z=1.96,
            p=0.5,
            q=0.5,
            error=0.05,
            tamano_documental_sugerido=(
                tamano_documental(len(poblacion)) if tipo == "DOCUMENTAL" else None
            ),
            confirmacion_institucional="PENDIENTE",
        ),
    )
    return {**datos, "huella_estudio": huella(datos)}


def obtener(db, estudio_id, bloquear=False):
    q = db.query(AuditoriaSistema).filter_by(id=estudio_id, accion=CREAR, recurso=RECURSO)
    if bloquear:
        q = q.populate_existing().with_for_update()
    estudio = q.first()
    if estudio is None:
        raise HTTPException(404, "Estudio no encontrado")
    datos = estudio.detalle or {}
    contenido = {k: v for k, v in datos.items() if k != "huella_estudio"}
    ids = [i["id"] for i in datos.get("items", [])]
    if (
        huella(contenido) != datos.get("huella_estudio")
        or not ids
        or len(ids) != len(set(ids))
        or ids
        != seleccionar(
            datos["poblacion_ids"],
            datos["tamano_solicitado"],
            datos["semilla"],
            datos.get("version", 1),
        )
        or datos.get("version", 1) not in (1, 2)
        or datos.get("metodo")
        != (METODO_V2 if datos.get("version", 1) == 2 else "sorteo_huella_semilla_id_v1")
    ):
        raise HTTPException(
            409, "El estudio perdió su integridad; no se publican métricas ni nuevas etiquetas."
        )
    return estudio


def ultimas(db, estudio_id):
    registros = (
        db.query(AuditoriaSistema)
        .filter_by(accion=ETIQUETAR, recurso=RECURSO, recurso_id=estudio_id)
        .order_by(AuditoriaSistema.id.desc())
    )
    resultado = {}
    for r in registros:
        resultado.setdefault(r.detalle["item_id"], r)
    return resultado


def cabecera(estudio):
    d = estudio.detalle
    return dict(
        id=estudio.id,
        tipo=d["tipo"],
        creada_en=estudio.fecha_hora,
        version=d.get("version", 1),
        criterios_referencia=d.get("criterios_referencia", {}),
        diseno_muestral=d.get("diseno_muestral"),
        creada_por=estudio.usuario_id,
        modelo_id=d["modelo_id"],
        modelo_huella=d["modelo_huella"],
        semilla=d["semilla"],
        referencia_protocolo=d["referencia_protocolo"],
        huella_estudio=d["huella_estudio"],
        poblacion=len(d["poblacion_ids"]),
        seleccionadas=len(d["items"]),
        metodo=d["metodo"],
        alcance=d["alcance"],
        publicacion_institucional="PENDIENTE",
    )


def foto_vigente(item, cache):
    ruta = item["documento"]["ruta_imagen_respaldo"]
    if ruta not in cache:
        cache[ruta] = foto_huella(ruta)
    return bool(item["foto_sha256"] and cache[ruta] == item["foto_sha256"])


def revision_publica(r):
    return dict(
        id=r.id,
        usuario_id=r.usuario_id,
        fecha=r.fecha_hora,
        **{k: r.detalle[k] for k in ("etiqueta", "motivo", "referencia", "independiente")},
        segunda_revision=r.detalle.get("segunda_revision", False),
        criterio=r.detalle.get("criterio"),
    )


def detalle_publico(db, estudio, usuario):
    d, revisiones, cache = estudio.detalle, ultimas(db, estudio.id), {}
    filas = []
    for item in d["items"]:
        revision = revisiones.get(item["id"])
        filas.append(
            dict(
                id=item["id"],
                documento=item["documento"],
                evidencia_vigente=foto_vigente(item, cache),
                revision=revision_publica(revision) if revision else None,
            )
        )
    return {
        **cabecera(estudio),
        "puede_etiquetar": usuario.id not in {estudio.usuario_id, d["entrenador_id"]}
        and usuario.rol.nombre in {"Administrador", "Auditor"},
        "filas": filas,
    }


def metricas(tipo, items, revisiones, completa, version=1):
    """Denominador congelado. null expresa pendiente o división indefinida."""
    if tipo == "DOCUMENTAL":
        coincidencias = sum(
            r.detalle["etiqueta"] == "COINCIDE_DOCUMENTO" for r in revisiones.values()
        )
        return dict(
            concordancia_filas=coincidencias / len(items) if completa and items else None,
            precision=None,
            recall=None,
            f1=None,
            matriz=None,
        )
    if not completa or not items:
        return dict(concordancia_filas=None, precision=None, recall=None, f1=None, matriz=None)
    matriz = Counter()
    for item in items:
        verdad = revisiones[item["id"]].detalle["etiqueta"] == (
            "ANOMALO" if version >= 2 else "INUSUAL_RELEVANTE"
        )
        pred = item["prediccion"]
        matriz["tp" if verdad and pred else "fn" if verdad else "fp" if pred else "tn"] += 1
    tp, fp, fn = matriz["tp"], matriz["fp"], matriz["fn"]

    def dividir(n, den):
        return n / den if den else None

    return dict(
        concordancia_filas=None,
        matriz={k: matriz[k] for k in ("tp", "fp", "fn", "tn")},
        precision=dividir(tp, tp + fp),
        recall=dividir(tp, tp + fn),
        f1=dividir(2 * tp, 2 * tp + fp + fn),
    )


def informe(db, estudio):
    d, rs, cache = estudio.detalle, ultimas(db, estudio.id), {}
    evidencias = sum(not foto_vigente(i, cache) for i in d["items"])
    independientes = {
        i["id"]: rs[i["id"]]
        for i in d["items"]
        if i["id"] in rs
        and rs[i["id"]].detalle.get("independiente") is True
        and rs[i["id"]].usuario_id not in {estudio.usuario_id, d["entrenador_id"]}
    }
    validas = {
        mid: r for mid, r in independientes.items() if r.detalle["etiqueta"] in conclusivas(d)
    }
    excluidas = {
        mid: r
        for mid, r in independientes.items()
        if d.get("version", 1) >= 2
        and r.detalle["etiqueta"] == indeterminada(d)
        and r.detalle.get("segunda_revision") is True
    }
    modelo_consistente = True
    if d["tipo"] == "DETECTOR":
        m = db.get(ModeloHistorico, d["modelo_id"])
        resultados = db.query(ResultadoHistorico).filter_by(modelo_id=d["modelo_id"]).all()
        por_id = {r.movimiento_id: r for r in resultados}
        modelo_consistente = bool(
            m
            and m.huella == d["modelo_huella"]
            and m.umbral == d["umbral"]
            and diagnosticar(m, resultados)["estado"] == "CONSISTENTE"
            and all(
                i["id"] in por_id
                and por_id[i["id"]].particion == "evaluacion"
                and por_id[i["id"]].alerta == i["prediccion"]
                for i in d["items"]
            )
        )
    completa = (
        len(validas) + len(excluidas) == len(d["items"]) and not evidencias and modelo_consistente
    )
    evaluables = [i for i in d["items"] if i["id"] in validas]
    return {
        **cabecera(estudio),
        "poblacion_ids": d["poblacion_ids"],
        "estado": (
            ("MUESTRA_COMPLETA" if validas else "SIN_CASOS_EVALUABLES") if completa else "PENDIENTE"
        ),
        "progreso": dict(
            seleccionadas=len(d["items"]),
            etiquetadas=len(rs),
            concluyentes=len(validas),
            pendientes=len(d["items"]) - len(validas) - len(excluidas),
            evidencias_no_vigentes=evidencias,
            indeterminados_excluidos=len(excluidas),
            denominador_principal=len(evaluables),
            modelo_consistente=modelo_consistente,
            etiquetas=dict(Counter(r.detalle["etiqueta"] for r in rs.values())),
        ),
        "metricas": metricas(d["tipo"], evaluables, validas, completa, d.get("version", 1)),
        "clase_positiva": "ANOMALO" if d.get("version", 1) >= 2 else "INUSUAL_RELEVANTE",
        "criterio_legacy": d.get("version", 1) == 1,
        "referencia_metricas": "https://scikit-learn.org/stable/modules/model_evaluation.html",
        "unidad": "Fila de la muestra; se conservan los lotes del corte, sin estimar independencia entre filas de una hoja.",
        "filas": [
            dict(
                id=i["id"],
                documento=i["documento"],
                foto_sha256=i["foto_sha256"],
                revision=revision_publica(rs[i["id"]]) if i["id"] in rs else None,
            )
            for i in d["items"]
        ],
    }
