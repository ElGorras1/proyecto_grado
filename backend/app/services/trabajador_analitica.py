"""Trabajador local persistente, coordinado con advisory lock de PostgreSQL."""

import hashlib
import logging
import os
import threading
from pathlib import Path

from sqlalchemy import text

from app.db.session import SessionLocal, engine
from app.models.auditoria import AuditoriaSistema
from app.models.auditoria_historica import ModeloHistorico, ResultadoHistorico, ahora

log = logging.getLogger(__name__)
ARTEFACTOS = Path(__file__).resolve().parents[2] / ".analytics"
LOCK_ID = 681940261
stop = threading.Event()
hilo = None


def evento(db, usuario, accion, modelo_id, detalle=None, ip=None):
    db.add(
        AuditoriaSistema(
            usuario_id=usuario,
            accion=accion,
            recurso="analitica_historica",
            resultado=(
                "error" if accion in ("ANALITICA_FALLIDA", "ANALITICA_INTERRUMPIDA") else "exito"
            ),
            fecha_hora=ahora(),
            ip_origen=ip,
            detalle={"modelo_id": modelo_id, **(detalle or {})},
        )
    )


def ejecutar(db, modelo_id, directorio=None):
    trabajo = db.get(ModeloHistorico, modelo_id)
    if not trabajo or trabajo.estado != "PENDIENTE":
        return
    trabajo.estado = "EN_EJECUCION"
    db.commit()
    try:
        import joblib

        from app.services.isolation_historico import calcular

        # La elegibilidad pertenece al corte, incluso si se despliega otra política
        # de selección mientras el trabajo está pendiente.
        excluidos = {id for ids in trabajo.corte["exclusiones"].values() for id in ids}
        filas = [f for f in trabajo.corte["filas"] if f["id"] not in excluidos]
        if len(filas) != trabajo.corte["perfil"]["elegibles"]:
            raise ValueError("El corte no coincide con su selección de datos conservada.")
        partes = None
        if trabajo.configuracion.get("modo") == "TEMPORAL":
            if not trabajo.corte["temporal"]["suficiente"]:
                raise ValueError("Datos insuficientes para separar años y grupos documentales. "
                                 "Consulta los faltantes del plan temporal.")
            partes = [trabajo.corte["particiones_temporales"][str(f["id"])] for f in filas]
        modelo, contexto, umbral, metricas, resultados = calcular(
            filas, trabajo.configuracion, partes=partes)
        carpeta = Path(directorio) if directorio else ARTEFACTOS
        carpeta.mkdir(parents=True, exist_ok=True)
        destino = carpeta / (modelo_id + ".joblib")
        temporal = carpeta / (modelo_id + ".tmp")
        # Solo objetos generados por este servidor; no hay endpoint de carga de modelos.
        fuentes = {
            p.name: p.read_text(encoding="utf-8-sig")
            for p in (
                Path(__file__),
                Path(__file__).with_name("isolation_historico.py"),
                Path(__file__).with_name("datos_analitica.py"),
            )
        }
        joblib.dump(
            {
                "modelo": modelo,
                "contexto": contexto,
                "umbral": umbral,
                "corte": trabajo.corte,
                "configuracion": trabajo.configuracion,
                "metricas": metricas,
                "fuentes": fuentes,
            },
            temporal,
        )
        os.replace(temporal, destino)
        # Si otro trabajador recuperó este trabajo tras perder el lock, no publicar.
        # El bloqueo de fila serializa publicación y recuperación de interrupciones.
        db.refresh(trabajo, with_for_update=True)
        if trabajo.estado != "EN_EJECUCION":
            db.rollback()
            return
        trabajo.artefacto_sha256 = hashlib.sha256(destino.read_bytes()).hexdigest()
        for resultado in resultados:
            f = resultado["snapshot"]
            db.add(
                ResultadoHistorico(
                    modelo_id=modelo_id,
                    movimiento_id=f["id"],
                    gestion=int(f["fecha"][:4]),
                    articulo_id=f["articulo_id"],
                    nodo=f["nodo_grafo"],
                    **resultado,
                )
            )
        trabajo.metricas = metricas
        trabajo.umbral = umbral
        trabajo.estado = "COMPLETADO"
        trabajo.plaza = None
        trabajo.terminado_en = ahora()
        evento(
            db,
            trabajo.usuario_id,
            "ANALITICA_COMPLETADA",
            modelo_id,
            {"evaluados": len(resultados), "alertas": metricas["alertas"]},
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        trabajo = db.get(ModeloHistorico, modelo_id)
        db.refresh(trabajo, with_for_update=True)
        if trabajo.estado != "EN_EJECUCION":
            # No reescribir un resultado confirmado o una recuperación previa.
            db.rollback()
            log.exception("El trabajo %s ya cambió de estado", modelo_id)
            return
        trabajo.estado = "INSUFICIENTE" if isinstance(exc, ValueError) else "FALLIDO"
        trabajo.error = (
            str(exc)
            if isinstance(exc, ValueError)
            else "Fallo de entrenamiento o persistencia. Consulta el registro del servidor."
        )
        trabajo.plaza = None
        trabajo.terminado_en = ahora()
        evento(db, trabajo.usuario_id, "ANALITICA_FALLIDA", modelo_id, {"estado": trabajo.estado})
        db.commit()
        log.exception("Entrenamiento %s no completado", modelo_id)


def recuperar_interrumpidos(db):
    # Se llama SOLO mientras poseemos el advisory lock: ningún otro trabajador está entrenando.
    for j in (
        db.query(ModeloHistorico)
        .filter(ModeloHistorico.estado == "EN_EJECUCION")
        .with_for_update()
        .all()
    ):
        j.estado, j.plaza = "FALLIDO", None
        j.error = "Entrenamiento interrumpido. Crea una nueva versión para reintentarlo."
        j.terminado_en = ahora()
        evento(db, j.usuario_id, "ANALITICA_INTERRUMPIDA", j.id)
    db.commit()


def ciclo():
    fallo_reportado = False
    while not stop.is_set():
        try:
            # El lock usa su propia conexión; los commits del trabajo no lo liberan.
            with engine.connect() as lock:
                adquirido = lock.scalar(text("SELECT pg_try_advisory_lock(:id)"), {"id": LOCK_ID})
                try:
                    if adquirido:
                        with SessionLocal() as db:
                            recuperar_interrumpidos(db)
                            j = (
                                db.query(ModeloHistorico)
                                .filter_by(estado="PENDIENTE")
                                .order_by(ModeloHistorico.creado_en)
                                .first()
                            )
                            if j:
                                ejecutar(db, j.id)
                    fallo_reportado = False
                finally:
                    if adquirido:
                        lock.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": LOCK_ID})
        except Exception:
            if not fallo_reportado:
                log.exception(
                    "Trabajador analítico no disponible; verificará conexión y "
                    "migración nuevamente."
                )
                fallo_reportado = True
        stop.wait(5)


def iniciar():
    global hilo
    if engine.dialect.name != "postgresql":
        return
    if hilo and hilo.is_alive():
        return
    stop.clear()
    hilo = threading.Thread(target=ciclo, name="analitica-historica", daemon=True)
    hilo.start()


def detener():
    stop.set()
