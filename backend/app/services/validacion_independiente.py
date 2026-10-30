"""Estudios congelados y etiquetas nuevas; no reutiliza decisiones HIL ni entrena."""
from collections import Counter
from hashlib import sha256

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
CONCLUSIVAS = {"DOCUMENTAL": {"COINCIDE_DOCUMENTO", "DIFERENCIA_DOCUMENTO"},
               "DETECTOR": {"LEGITIMO", "INUSUAL_RELEVANTE"}}
CAMPOS = ("id", "articulo_id", "articulo", "codigo", "lote_id", "numero_pagina", "orden_fila",
          "fecha", "fecha_documental_texto", "fecha_precision", "detalle", "referencia", "area",
          "ingresos", "salidas", "saldo_registrado", "ruta_imagen_respaldo")
ALCANCE = ("Resultados del corte y la muestra seleccionada, sin extrapolación al archivo completo. "
           "La concordancia de transcripción vigente no mide CER/WER del OCR original. "
           "Inusual relevante no significa fraude. No se reajusta el umbral con evaluación reservada.")


def seleccionar(ids, tamano, semilla):
    """Sorteo por huella de semilla/ID, sin consultar etiquetas ni puntuaciones."""
    return sorted(set(ids), key=lambda i: (sha256(f"{semilla}:{i}".encode()).digest(), i))[:tamano]


def crear_datos(db, tipo, modelo_id, tamano, semilla, referencia_protocolo):
    modelo = None
    if tipo == "DETECTOR":
        modelo = db.get(ModeloHistorico, modelo_id)
        if modelo is None:
            raise HTTPException(404, "Modelo no encontrado")
        resultados = db.query(ResultadoHistorico).filter_by(modelo_id=modelo.id).all()
        if diagnosticar(modelo, resultados)["estado"] != "CONSISTENTE":
            raise HTTPException(409, "El modelo y su corte deben estar completos y ser consistentes.")
        poblacion = {f.movimiento_id: f for f in resultados if f.particion == "evaluacion"}
    else:
        poblacion = {m.id: (m, a) for m, a in db.query(MovimientoKardex, Activo).join(
            Activo, Activo.id == MovimientoKardex.articulo_id).filter(
            MovimientoKardex.lote_id.isnot(None), MovimientoKardex.estado == "ACTIVO",
            MovimientoKardex.ruta_imagen_respaldo.isnot(None), MovimientoKardex.ruta_imagen_respaldo != "")}
    if not poblacion:
        raise HTTPException(409, "No hay filas disponibles en la población de este estudio.")
    ids = seleccionar(poblacion, tamano, semilla)
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
    datos = dict(version=1, tipo=tipo, semilla=semilla, referencia_protocolo=referencia_protocolo,
        metodo="sorteo_huella_semilla_id_v1", tamano_solicitado=tamano,
        poblacion_ids=sorted(poblacion), items=items,
        modelo_id=modelo.id if modelo else None, modelo_huella=modelo.huella if modelo else None,
        entrenador_id=modelo.usuario_id if modelo else None,
        umbral=modelo.umbral if modelo else None,
        alcance=ALCANCE, publicacion_institucional="PENDIENTE")
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
    if (huella(contenido) != datos.get("huella_estudio") or not ids or len(ids) != len(set(ids))
            or ids != seleccionar(datos["poblacion_ids"], datos["tamano_solicitado"], datos["semilla"])):
        raise HTTPException(409, "El estudio perdió su integridad; no se publican métricas ni nuevas etiquetas.")
    return estudio


def ultimas(db, estudio_id):
    registros = db.query(AuditoriaSistema).filter_by(accion=ETIQUETAR, recurso=RECURSO,
        recurso_id=estudio_id).order_by(AuditoriaSistema.id.desc())
    resultado = {}
    for r in registros:
        resultado.setdefault(r.detalle["item_id"], r)
    return resultado


def cabecera(estudio):
    d = estudio.detalle
    return dict(id=estudio.id, tipo=d["tipo"], creada_en=estudio.fecha_hora,
        creada_por=estudio.usuario_id, modelo_id=d["modelo_id"], modelo_huella=d["modelo_huella"], semilla=d["semilla"],
        referencia_protocolo=d["referencia_protocolo"], huella_estudio=d["huella_estudio"],
        poblacion=len(d["poblacion_ids"]), seleccionadas=len(d["items"]),
        metodo=d["metodo"], alcance=d["alcance"], publicacion_institucional="PENDIENTE")


def foto_vigente(item, cache):
    ruta = item["documento"]["ruta_imagen_respaldo"]
    if ruta not in cache:
        cache[ruta] = foto_huella(ruta)
    return bool(item["foto_sha256"] and cache[ruta] == item["foto_sha256"])


def revision_publica(r):
    return dict(id=r.id, usuario_id=r.usuario_id, fecha=r.fecha_hora,
        **{k: r.detalle[k] for k in ("etiqueta", "motivo", "referencia", "independiente")})


def detalle_publico(db, estudio, usuario):
    d, revisiones, cache = estudio.detalle, ultimas(db, estudio.id), {}
    filas = []
    for item in d["items"]:
        revision = revisiones.get(item["id"])
        filas.append(dict(id=item["id"], documento=item["documento"],
            evidencia_vigente=foto_vigente(item, cache),
            revision=revision_publica(revision) if revision else None))
    return {**cabecera(estudio), "puede_etiquetar": usuario.id not in {
        estudio.usuario_id, d["entrenador_id"]} and usuario.rol.nombre in {"Administrador", "Auditor"},
        "filas": filas}


def metricas(tipo, items, revisiones, completa):
    """Denominador congelado. null expresa pendiente o división indefinida."""
    if tipo == "DOCUMENTAL":
        coincidencias = sum(r.detalle["etiqueta"] == "COINCIDE_DOCUMENTO" for r in revisiones.values())
        return dict(concordancia_filas=coincidencias / len(items) if completa else None,
            precision=None, recall=None, f1=None, matriz=None)
    if not completa:
        return dict(concordancia_filas=None, precision=None, recall=None, f1=None, matriz=None)
    matriz = Counter()
    for item in items:
        verdad = revisiones[item["id"]].detalle["etiqueta"] == "INUSUAL_RELEVANTE"
        pred = item["prediccion"]
        matriz["tp" if verdad and pred else "fn" if verdad else "fp" if pred else "tn"] += 1
    tp, fp, fn = matriz["tp"], matriz["fp"], matriz["fn"]
    def dividir(n, den):
        return n / den if den else None
    return dict(concordancia_filas=None, matriz={k: matriz[k] for k in ("tp", "fp", "fn", "tn")},
        precision=dividir(tp, tp + fp), recall=dividir(tp, tp + fn), f1=dividir(2 * tp, 2 * tp + fp + fn))


def informe(db, estudio):
    d, rs, cache = estudio.detalle, ultimas(db, estudio.id), {}
    evidencias = sum(not foto_vigente(i, cache) for i in d["items"])
    validas = {i["id"]: rs[i["id"]] for i in d["items"] if i["id"] in rs
        and rs[i["id"]].detalle["etiqueta"] in CONCLUSIVAS[d["tipo"]]
        and rs[i["id"]].detalle.get("independiente") is True
        and rs[i["id"]].usuario_id not in {estudio.usuario_id, d["entrenador_id"]}}
    modelo_consistente = True
    if d["tipo"] == "DETECTOR":
        m = db.get(ModeloHistorico, d["modelo_id"])
        resultados = db.query(ResultadoHistorico).filter_by(modelo_id=d["modelo_id"]).all()
        por_id = {r.movimiento_id: r for r in resultados}
        modelo_consistente = bool(m and m.huella == d["modelo_huella"] and m.umbral == d["umbral"]
            and diagnosticar(m, resultados)["estado"] == "CONSISTENTE"
            and all(i["id"] in por_id and por_id[i["id"]].particion == "evaluacion"
                and por_id[i["id"]].alerta == i["prediccion"] for i in d["items"]))
    completa = len(validas) == len(d["items"]) and not evidencias and modelo_consistente
    return {**cabecera(estudio), "poblacion_ids": d["poblacion_ids"],
        "estado": "MUESTRA_COMPLETA" if completa else "PENDIENTE",
        "progreso": dict(seleccionadas=len(d["items"]), etiquetadas=len(rs), concluyentes=len(validas),
            pendientes=len(d["items"]) - len(validas), evidencias_no_vigentes=evidencias,
            modelo_consistente=modelo_consistente,
            etiquetas=dict(Counter(r.detalle["etiqueta"] for r in rs.values()))),
        "metricas": metricas(d["tipo"], d["items"], validas, completa),
        "referencia_metricas": "https://scikit-learn.org/stable/modules/model_evaluation.html",
        "unidad": "Fila de la muestra; se conservan los lotes del corte, sin estimar independencia entre filas de una hoja.",
        "filas": [dict(id=i["id"], documento=i["documento"], foto_sha256=i["foto_sha256"],
            revision=revision_publica(rs[i["id"]]) if i["id"] in rs else None) for i in d["items"]]}
