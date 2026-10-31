"""Inferencia con pesos conservados y revisión periódica; nunca rectifica el Kárdex."""

from copy import deepcopy
from collections import Counter
from datetime import UTC, datetime, timedelta
import hashlib
import logging
import math
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import inspect
from app.models.automatizacion_analitica import PoliticaAnalitica, ResultadoSeguimiento
from app.models.auditoria_historica import ModeloHistorico, ResultadoHistorico
from app.schemas.analitica import EntrenamientoHistorico
from app.services.datos_analitica import huella, leer_corte, seleccionar
from app.services.particiones_articulo import particionar_por_articulo

log = logging.getLogger(__name__)
ARTEFACTOS = Path(__file__).resolve().parents[2] / ".analytics"


def utc(valor):
    return valor.replace(tzinfo=UTC) if valor.tzinfo is None else valor.astimezone(UTC)


def elegibles_del_corte(corte, hasta):
    excluidos = {i for ids in corte["exclusiones"].values() for i in ids}
    return [
        f
        for f in corte["filas"]
        if f["id"] not in excluidos and f.get("fecha") and 1900 <= int(f["fecha"][:4]) <= hasta
    ]


def huella_entrenamiento(filas):
    # Cambiar un texto administrativo no obliga a volver a ajustar los árboles.
    campos = (
        "id",
        "articulo_id",
        "lote_id",
        "numero_pagina",
        "orden_fila",
        "ruta_imagen_respaldo",
        "nodo_grafo",
        "ingresos",
        "salidas",
        "fecha",
    )
    return huella([{k: f.get(k) for k in campos} for f in sorted(filas, key=lambda x: x["id"])])


def modelo_referencia(db):
    politica = db.get(PoliticaAnalitica, 1)
    if politica:
        return db.get(ModeloHistorico, politica.modelo_base_id)
    return next(
        (
            m
            for m in db.query(ModeloHistorico)
            .filter_by(estado="COMPLETADO")
            .order_by(ModeloHistorico.creado_en.desc(), ModeloHistorico.id)
            if not m.configuracion.get("candidato_automatico")
        ),
        None,
    )


def cargar_modelo(modelo, directorio=None):
    import joblib

    assert str(UUID(modelo.id)) == modelo.id
    if modelo.estado != "COMPLETADO" or modelo.umbral is None or not modelo.artefacto_sha256:
        raise ValueError("La versión de referencia no está disponible para analizar.")
    raiz = Path(directorio) if directorio else ARTEFACTOS
    ruta = raiz / (modelo.id + ".joblib")
    if ruta.resolve().parent != raiz.resolve():
        raise ValueError("La ruta del modelo no es válida.")
    datos = ruta.read_bytes()
    if hashlib.sha256(datos).hexdigest() != modelo.artefacto_sha256:
        raise ValueError("El archivo del modelo no coincide con su huella.")
    # Bytes verificados: no volver a abrir una ruta que podría cambiar entre comprobación y carga.
    import io

    artefacto = joblib.load(io.BytesIO(datos))
    if artefacto["umbral"] != modelo.umbral or artefacto["configuracion"] != modelo.configuracion:
        raise ValueError("El artefacto no coincide con la configuración conservada.")
    return artefacto


def inferir(db, politica, modelo, filas, instante, directorio=None):
    originales = {
        r.movimiento_id: r.snapshot
        for r in db.query(ResultadoHistorico).filter_by(modelo_id=modelo.id)
    }
    existentes = {
        (r.movimiento_id, r.huella_snapshot)
        for r in db.query(
            ResultadoSeguimiento.movimiento_id, ResultadoSeguimiento.huella_snapshot
        ).filter_by(modelo_id=modelo.id)
    }
    pendientes = [
        (f, huella(f))
        for f in filas
        if originales.get(f["id"]) != f and (f["id"], huella(f)) not in existentes
    ]
    if not pendientes:
        return dict(elegibles=len(filas), nuevos_resultados=0, nuevos_avisos=0)
    a = cargar_modelo(modelo, directorio)
    matriz, contextos = a["contexto"].transformar([f for f, _ in pendientes])
    scores = -a["modelo"].score_samples(matriz)
    for (f, digest), contexto, score in zip(pendientes, contextos, scores, strict=True):
        score = float(score)
        if not math.isfinite(score):
            raise ValueError("La puntuación calculada no es finita.")
        db.add(
            ResultadoSeguimiento(
                modelo_id=modelo.id,
                movimiento_id=f["id"],
                articulo_id=f["articulo_id"],
                gestion=int(f["fecha"][:4]),
                creado_en=instante,
                huella_snapshot=digest,
                snapshot=f,
                contexto=contexto,
                score=score,
                alerta=score > modelo.umbral,
            )
        )
    return dict(
        elegibles=len(filas),
        nuevos_resultados=len(pendientes),
        nuevos_avisos=sum(float(s) > modelo.umbral for s in scores),
    )


def revisar_actualizacion(db, politica, modelo, corte, filas, instante):
    if politica.ultima_revision and instante < utc(politica.ultima_revision) + timedelta(
        days=politica.revision_dias
    ):
        return (politica.ultimo_informe or {}).get("mantenimiento", {"estado": "PROGRAMADO"})
    politica.ultima_revision = instante
    fingerprint = huella_entrenamiento(filas)
    referencia = politica.huella_revision or huella_entrenamiento(
        elegibles_del_corte(modelo.corte, politica.gestion_hasta)
    )
    politica.huella_revision = fingerprint
    if referencia == fingerprint:
        return dict(
            estado="SIN_CAMBIOS",
            mensaje="Los datos de entrenamiento no cambiaron; no se crea otra versión.",
        )
    if not politica.preparar_candidatos:
        return dict(
            estado="ACTUALIZACION_DESACTIVADA",
            mensaje="Hay cambios; la preparación automática de versiones está desactivada.",
        )
    if politica.candidato_id:
        previo = db.get(ModeloHistorico, politica.candidato_id)
        if (
            previo
            and huella_entrenamiento(elegibles_del_corte(previo.corte, politica.gestion_hasta))
            == fingerprint
        ):
            return dict(
                estado="CANDIDATO_EXISTENTE",
                mensaje="Ya existe una versión preparada con estos datos; se conserva para evaluación técnica.",
                modelo_id=previo.id,
            )
    if db.query(ModeloHistorico.id).filter_by(plaza=1).first():
        # No consumir la revisión: el próximo ciclo reintentará cuando quede libre.
        politica.ultima_revision = None
        politica.huella_revision = referencia
        return dict(
            estado="TRABAJO_EN_CURSO",
            mensaje="Ya hay un trabajo en curso; se mantiene el modelo disponible.",
        )
    try:
        partes = Counter(particionar_por_articulo(filas, 42))
        if partes["entrenamiento"] < 50 or partes["calibracion"] < 20 or partes["evaluacion"] < 20:
            raise ValueError("Faltan filas en las particiones.")
    except ValueError:
        return dict(
            estado="MUESTRA_INSUFICIENTE",
            mensaje="Los cambios todavía no permiten preparar una versión con grupos independientes suficientes.",
        )
    nuevo_corte = deepcopy(corte)
    permitidos = {f["id"] for f in filas}
    elegibles_actuales, _ = seleccionar(corte["filas"])
    fuera = [f["id"] for f in elegibles_actuales if f["id"] not in permitidos]
    if fuera:
        nuevo_corte["exclusiones"]["fuera_alcance_automatico"] = fuera
    nuevo_corte["perfil"]["elegibles"] = len(filas)
    for gestion, datos in nuevo_corte["perfil"]["por_gestion"].items():
        datos["elegibles"] = sum(f["fecha"][:4] == gestion for f in filas)
    for articulo, datos in nuevo_corte["perfil"]["por_articulo"].items():
        datos["elegibles"] = sum(str(f["articulo_id"]) == str(articulo) for f in filas)
    config = EntrenamientoHistorico(modo="POR_ARTICULO").model_dump()
    config["candidato_automatico"] = True
    nuevo = ModeloHistorico(
        id=str(uuid4()),
        estado="PENDIENTE",
        plaza=1,
        usuario_id=None,
        configuracion=config,
        corte=nuevo_corte,
        huella=huella(nuevo_corte["filas"]),
    )
    db.add(nuevo)
    db.flush()
    politica.candidato_id = nuevo.id
    from app.services.trabajador_analitica import evento

    evento(
        db,
        None,
        "ANALITICA_CANDIDATA_AUTOMATICA",
        nuevo.id,
        {"modelo_base_id": modelo.id, "huella_entrenamiento": fingerprint},
    )
    return dict(
        estado="CANDIDATO_PREPARADO",
        mensaje="Se preparó una versión para evaluación técnica. El modelo en uso se conserva.",
        modelo_id=nuevo.id,
    )


def ejecutar_ciclo(db, *, instante=None, directorio=None, forzar=False):
    instante = utc(instante or datetime.now(UTC))
    politica = db.query(PoliticaAnalitica).filter_by(id=1).with_for_update().first()
    if not politica or not politica.habilitada:
        return None
    if (
        not forzar
        and politica.ultimo_analisis
        and instante
        < utc(politica.ultimo_analisis) + timedelta(seconds=politica.intervalo_segundos)
    ):
        return None
    try:
        modelo = db.get(ModeloHistorico, politica.modelo_base_id)
        if not modelo or modelo.estado != "COMPLETADO":
            raise ValueError("No hay una versión de referencia completada.")
        corte = leer_corte(db)
        filas = elegibles_del_corte(corte, politica.gestion_hasta)
        resumen = inferir(db, politica, modelo, filas, instante, directorio)
        mantenimiento = revisar_actualizacion(db, politica, modelo, corte, filas, instante)
        politica.ultimo_informe = {
            **resumen,
            "mantenimiento": mantenimiento,
            "modelo_base_id": modelo.id,
            "alcance_hasta": politica.gestion_hasta,
        }
        politica.ultimo_analisis = instante
        politica.ultimo_error = None
        db.commit()
        return politica.ultimo_informe
    except Exception:
        db.rollback()
        log.exception("No se completó el seguimiento automático; se conservó el modelo y el corte.")
        politica = db.get(PoliticaAnalitica, 1)
        if politica:
            politica.ultimo_error = "No se completó el análisis automático. Se conserva el modelo anterior; revisar el mantenimiento técnico."
            politica.ultimo_analisis = instante  # Evita repetir un fallo cada cinco segundos.
            db.commit()
        return None


def esquema_disponible(db):
    return inspect(db.get_bind()).has_table("politica_analitica")
