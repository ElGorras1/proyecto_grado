"""Asignación histórica por similitud y contexto; no confirma identidad institucional."""
from collections import Counter, defaultdict
import re
import unicodedata
from thefuzz import fuzz

VERSION = "correlacion-areas-v1"


def normalizar(texto):
    plano = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9+]", "", plano.upper())


def proponer_area(texto, catalogo, frecuencias, por_articulo, por_pagina):
    """La frecuencia desempata candidatos parecidos; no reemplaza un texto diferente.

    Los índices contienen solo nombres/alias confirmados antes de esta ejecución.
    Ni las sugerencias previas ni las inferencias de este plan se realimentan.
    Los niveles de soporte son reglas descriptivas, no probabilidades de acierto.
    """
    literal = normalizar(texto)
    if len(literal) < 2:
        return {"area": None, "motivo": "Sin letras suficientes para comparar.", "candidatos": []}
    if literal in {"SALIDA", "SALIDAS", "INGRESO", "INGRESOS", "VENTA", "VENTAS",
                   "CONSIG", "CONSIGNACION", "OBSEQUIO", "DONACION", "DEVOLUCION"}:
        return {"area": None, "motivo": "El texto describe una operación, no una variante de área.", "candidatos": []}
    areas = [c for c in catalogo if c["tipo"] == "departamento"]
    candidatos = []
    for c in areas:
        formas = [normalizar(c["nombre_oficial"]), normalizar(c.get("abreviatura"))]
        semejanza_textual = max(fuzz.ratio(literal, f) / 100 for f in formas if f)
        semejanza = semejanza_textual
        regla = "parecido_y_frecuencia"
        nombre = c["nombre_oficial"]
        if nombre == "C+C" and re.fullmatch(r"C[TYF+]C", literal):
            semejanza, regla = 0.98, "variante_grafica_C+C"
        elif nombre == "Capacitación" and literal in {"COP", "CDP"}:
            semejanza, regla = 0.90, "familia_CAP_COP_CDP"
        elif nombre == "Galería" and literal in {"GALS", "GOLS", "GALERIALIBRERIA"}:
            semejanza, regla = 0.94, "variante_GAL_y_contexto"
        elif nombre == "Sala" and literal == "SALAEXP":
            semejanza, regla = 0.94, "abreviacion_Sala_Exp"
        elif nombre == "CID" and literal == "CIO":
            semejanza, regla = 0.90, "variante_CID_CIO"
        # Un truncamiento CEDO no distingue CEDOAL de CEDOC. Se comparan ambos
        # contra la frecuencia del artículo/hoja, sin fusionar los dos catálogos.
        elif nombre in {"CEDOAL", "CEDOC"} and literal.startswith("CEDO"):
            semejanza = max(semejanza, 0.80)
            regla = "familia_CEDO_contextual"
        local = por_articulo.get(nombre, 0) / max(sum(por_articulo.values()), 1)
        pagina = por_pagina.get(nombre, 0) / max(sum(por_pagina.values()), 1)
        global_ = frecuencias.get(nombre, 0) / max(sum(frecuencias.values()), 1)
        score = 0.70 * semejanza + 0.16 * local + 0.10 * pagina + 0.04 * global_
        candidatos.append({"area": nombre, "area_id": c["id"], "activa": c["activa"],
                           "semejanza_textual": semejanza_textual,
                           "afinidad_regla": round(semejanza, 3), "puntuacion": round(score, 4),
                           "frecuencia_global": frecuencias.get(nombre, 0),
                           "frecuencia_articulo": por_articulo.get(nombre, 0),
                           "frecuencia_pagina": por_pagina.get(nombre, 0), "regla": regla})
    # Primero se exige parecido. CEDOAL no puede ganar por volumen si no se parece.
    exactos = [c for c in candidatos if c["semejanza_textual"] == 1]
    elegibles = exactos or [c for c in candidatos if c["afinidad_regla"] >= 0.78]
    ranking = sorted(elegibles, key=lambda c: (-c["puntuacion"], -c["afinidad_regla"], c["area_id"]))
    todos = sorted(candidatos, key=lambda c: (-c["puntuacion"], c["area_id"]))
    if not ranking:
        return {"area": None, "motivo": "Ningún área alcanza el parecido mínimo; la frecuencia sola no prueba equivalencia.",
                "candidatos": todos[:3]}
    primero = ranking[0]
    margen = primero["puntuacion"] - ranking[1]["puntuacion"] if len(ranking) > 1 else None
    if margen is not None and margen < 0.035 and primero["afinidad_regla"] < 1:
        return {"area": None, "motivo": "Empate entre áreas parecidas; contexto insuficiente.",
                "candidatos": ranking[:3]}
    motivos = {
        "parecido_y_frecuencia": "Parecido del texto, ponderado por frecuencia en el artículo, la hoja y el archivo",
        "variante_grafica_C+C": "Grafía compatible con C+C, área histórica cerrada confirmada por el titular",
        "familia_CAP_COP_CDP": "Agrupación propuesta CAP/COP/CDP, con ponderación de las frecuencias del artículo y la hoja",
        "variante_GAL_y_contexto": "Variante de GAL/Galería, con ponderación del contexto de la hoja",
        "abreviacion_Sala_Exp": "Abreviación compatible con Sala de Exhibiciones",
        "variante_CID_CIO": "Variante gráfica propuesta CIO/CID",
        "familia_CEDO_contextual": "Variante CEDO comparada con CEDOC y CEDOAL según el contexto local",
    }
    return {**primero, "soporte": "ALTO" if primero["afinidad_regla"] >= 0.94 else "MEDIO",
            "motivo": motivos[primero["regla"]] + "; identidad no confirmada.",
            "candidatos": ranking[:3], "version": VERSION}


def construir_indices(filas, catalogo, aliases):
    """Usa área literal incluso cuando el nodo prioriza Ventas/Feria/Obsequios."""
    areas = {c["id"]: c for c in catalogo if c["tipo"] == "departamento"}
    mapa = {}
    for c in areas.values():
        for valor in (c["nombre_oficial"], c.get("abreviatura")):
            if valor:
                mapa[normalizar(valor)] = c["nombre_oficial"]
    for a in aliases:
        if a["confirmado"] and a["area_oficial_id"] in areas:
            mapa[normalizar(a["texto_sucio"])] = areas[a["area_oficial_id"]]["nombre_oficial"]
    globales = Counter()
    articulos, paginas = defaultdict(Counter), defaultdict(Counter)
    for f in filas:
        if f["lote_id"] is None or f["estado"] != "ACTIVO":
            continue
        # Una lectura pendiente puede ser CAP/CID sobreescrita: no se vota a sí misma.
        if f["requiere_auditoria_nodo"] or f["area_estado"] in {"PENDIENTE_HIL", "AREA_NO_CATALOGADA"}:
            continue
        nombre = mapa.get(normalizar(f["area"]))
        if nombre:
            globales[nombre] += 1
            articulos[f["articulo_id"]][nombre] += 1
            if f["ruta_imagen_respaldo"]:
                paginas[f["ruta_imagen_respaldo"]][nombre] += 1
    return globales, articulos, paginas


def aplicar_asignacion(m, propuesta, *, plan_sha256, autor, registrado_en):
    """Aplica solo una clasificación inferida; la lectura y las demás marcas siguen.

    El llamador bloquea/verifica la fila y registra previo/nuevo en la misma
    transacción. No crea alias globales: una inferencia es específica de su fila.
    """
    from copy import deepcopy
    from app.services.calidad_kardex import tipos_alerta
    from app.services.tratamiento_hil import huella_datos, resumen_tratamiento

    if m.lote_id is None or m.estado != "ACTIVO":
        raise ValueError("Solo se asignan áreas de movimientos históricos activos")
    if propuesta.get("version") != VERSION or not propuesta.get("area"):
        raise ValueError("Propuesta histórica incompleta")
    revision = deepcopy(m.revision_documental or {})
    anterior = revision.get("asignacion_area", {})
    if anterior.get("plan_sha256") == plan_sha256 and anterior.get("estado") == "INFERIDA":
        if anterior.get("area") != propuesta["area"] or m.nodo_grafo != "Área: " + propuesta["area"]:
            raise ValueError("La asignación aplicada difiere del plan")
        return False
    tratamiento = resumen_tratamiento(m)
    if not tratamiento or tratamiento["estado"] != "CATEGORIZADO_CON_MARCA" or "area" not in tipos_alerta(m):
        raise ValueError("La fila requiere un tratamiento previo vigente de área")
    m.nodo_grafo = "Área: " + propuesta["area"]
    m.area_estado = "PENDIENTE_HIL"
    m.requiere_auditoria_nodo = True
    revision["asignacion_area"] = {**deepcopy(propuesta), "estado": "INFERIDA", "literal": m.area,
                                   "plan_sha256": plan_sha256, "autor": autor,
                                   "registrado_en": registrado_en}
    m.revision_documental = revision
    decisiones = deepcopy(revision["tratamiento_hil"]["decisiones"])
    for d in decisiones:
        if d["campo"] == "area":
            d.update(categoria="ASIGNACION_INFERIDA", criterios=sorted(set(d["criterios"] + ["T17-CORRELACION-20261028"])),
                     motivo=f"Lectura conservada {m.area!r}; área asignada {propuesta['area']!r}. "
                            + propuesta["motivo"] + " Se mantienen la marca y la exclusión analítica.")
    revision["tratamiento_hil"] = {"version": 1, "avisos": tipos_alerta(m),
                                  "huella_datos": huella_datos(m), "decisiones": decisiones,
                                  "autor": autor, "categorizado_en": registrado_en}
    m.revision_documental = revision
    return True
