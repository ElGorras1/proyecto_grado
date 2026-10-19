"""Analítica de registros actuales. Activación explícita y reglas de stock intactas."""

import hashlib
import os
from contextlib import contextmanager
from typing import Literal
from uuid import uuid4

import joblib
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.activos import Activo
from app.models.analitica_operativa import ModeloOperativo, ResultadoOperativo
from app.models.inventario import CustodiaExterna, EventoCustodiaExterna, TransferenciaArea
from app.models.kardex import MovimientoKardex
from app.services import analitica_operativa as servicio
from app.services.datos_analitica import huella
from app.services.inventario import auditar
from app.services.periodos import limites_gestion

router = APIRouter(prefix="/analitica-operativa", tags=["Analítica de inventario actual"])
lector = require_roles("Administrador", "Auditor", "Operador")
admin = require_roles("Administrador")


class Configuracion(BaseModel):
    arboles: int = Field(100, ge=100, le=300)
    semilla: int = Field(42, ge=0, le=2147483646)
    porcentaje_revision: float = Field(5, ge=1, le=20)


class Motivo(BaseModel):
    motivo: str = Field(min_length=10, max_length=2000, pattern=r"\S.*\S")

    @field_validator("motivo")
    @classmethod
    def validar(cls, v):
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Explica el motivo con al menos diez caracteres.")
        return v


@contextmanager
def bloqueo(db, clave=681940262):
    if db.bind.dialect.name != "postgresql":
        yield
        return
    with db.bind.connect() as con:
        adquirido = con.scalar(text("SELECT pg_try_advisory_lock(:clave)"), {"clave": clave})
        if not adquirido:
            raise HTTPException(409, "Otro entrenamiento o activación operativa está en proceso.")
        try:
            yield
        finally:
            con.execute(text("SELECT pg_advisory_unlock(:clave)"), {"clave": clave})


def publico(m):
    return dict(
        id=m.id,
        estado=m.estado,
        activo=m.activo == 1,
        creado_en=m.creado_en,
        configuracion=m.configuracion,
        metricas=m.metricas,
        umbral=m.umbral,
        huella=m.huella,
        error=m.error,
    )


@router.get("/perfil")
def perfil(db: Session = Depends(get_db), _=Depends(lector)):
    filas, exclusiones = servicio.capturar(db)
    m = db.query(ModeloOperativo).filter_by(activo=1).first()
    suficientes = len(filas) >= servicio.MINIMO
    motivo = "Faltan operaciones digitales reales para entrenar." if not suficientes else None
    if suficientes:
        try:
            servicio.dividir(filas)
        except ValueError as e:
            suficientes = False
            motivo = str(e)
    disponible = False
    if m:
        try:
            servicio.cargar(m)
            disponible = True
        except servicio.ERRORES_MODELO:
            pass
    return dict(
        total=len(filas),
        minimo=servicio.MINIMO,
        faltantes=max(0, servicio.MINIMO - len(filas)),
        suficientes=suficientes,
        exclusiones=exclusiones,
        minimo_dias=servicio.MIN_DIAS,
        motivo_insuficiencia=motivo,
        modelo_activo=publico(m) if m else None,
        modelo_disponible=disponible,
        controles_deterministicos_activos=True,
        estado="MODELO_PROVISIONAL_ACTIVO" if disponible else "CONTROLES_ACTIVOS_SIN_MODELO",
        advertencia="Solo se usan operaciones digitales posteriores a apertura, con fecha "
        "de hecho y registro conocidas. No se usan escaneos OCR ni se infieren "
        "horas o responsables antiguos. El modelo requiere revisión humana.",
    )


@router.get("/modelos")
def listar(
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(lector),
):
    q = db.query(ModeloOperativo)
    return {
        "total": q.count(),
        "filas": [
            publico(m)
            for m in q.order_by(ModeloOperativo.creado_en.desc())
            .offset((pagina - 1) * limite)
            .limit(limite)
        ],
    }


@router.post("/entrenar", status_code=201)
def entrenar(
    config: Configuracion, request: Request, db: Session = Depends(get_db), usuario=Depends(admin)
):
    with bloqueo(db):
        # Si el proceso terminó, su advisory lock ya no existe: el trabajo se marca interrumpido.
        for anterior in db.query(ModeloOperativo).filter_by(plaza=1).with_for_update():
            anterior.estado, anterior.plaza = "FALLIDO", None
            anterior.error = "Entrenamiento interrumpido; prepara una versión nueva."
            auditar(
                db,
                usuario,
                request,
                "modelo_operativo_interrumpido",
                "analitica_operativa",
                None,
                {"modelo_id": anterior.id},
            )
        db.commit()
        filas, _ = servicio.capturar(db)
        try:
            servicio.dividir(filas)
        except ValueError as e:
            raise HTTPException(422, str(e))
        m = ModeloOperativo(
            id=str(uuid4()),
            estado="EN_EJECUCION",
            plaza=1,
            usuario_id=usuario.id,
            configuracion=config.model_dump(),
            corte=filas,
            huella=huella(filas),
        )
        db.add(m)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Hay otro entrenamiento operativo en proceso.")
        try:
            a, metricas = servicio.calcular(filas, config.model_dump())
            servicio.ARTEFACTOS.mkdir(parents=True, exist_ok=True)
            temporal = servicio.ARTEFACTOS / (m.id + ".tmp")
            destino = servicio.ARTEFACTOS / (m.id + ".joblib")
            joblib.dump(a, temporal)
            os.replace(temporal, destino)
            m.artefacto_sha256 = hashlib.sha256(destino.read_bytes()).hexdigest()
            m.metricas, m.umbral, m.estado, m.plaza = metricas, a["umbral"], "COMPLETADO", None
            auditar(
                db,
                usuario,
                request,
                "entrenar_modelo_operativo",
                "analitica_operativa",
                None,
                {"modelo_id": m.id, "huella": m.huella, "metricas": metricas},
            )
            db.commit()
        except Exception:
            db.rollback()
            db.refresh(m)
            if m.estado != "COMPLETADO":
                m.estado, m.plaza = "FALLIDO", None
                m.error = "No se pudo completar el modelo. Consulta el registro del servicio."
                db.commit()
            servicio.log.exception("Entrenamiento operativo no completado")
            raise HTTPException(
                503, "Entrenamiento no completado; controles inmediatos siguen activos."
            )
        return publico(m)


@router.post("/modelos/{id}/{accion}")
def cambiar_modelo(
    id: str,
    accion: Literal["activar", "desactivar"],
    motivo: Motivo,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(admin),
):
    with bloqueo(db):
        m = db.query(ModeloOperativo).filter_by(id=id).with_for_update().first()
        if not m:
            raise HTTPException(404, "Modelo no encontrado")
        if accion == "activar":
            if m.estado != "COMPLETADO":
                raise HTTPException(409, "El modelo no está completado")
            try:
                servicio.cargar(m)
            except servicio.ERRORES_MODELO:
                raise HTTPException(409, "El archivo privado no está disponible o es incompatible")
            if m.activo == 1:
                return publico(m)
            for otro in db.query(ModeloOperativo).filter_by(activo=1).with_for_update():
                otro.activo = None
            db.flush()
            m.activo = 1
        else:
            if m.activo is None:
                return publico(m)
            m.activo = None
        auditar(
            db,
            usuario,
            request,
            accion + "_modelo_operativo",
            "analitica_operativa",
            None,
            {
                "modelo_id": m.id,
                "motivo": motivo.motivo.strip(),
                "estado_validacion": "PROVISIONAL",
            },
        )
        db.commit()
        return publico(m)


@router.get("/resultados")
def resultados(
    modelo_id: str | None = None,
    alertas: bool = False,
    gestion: int | None = Query(None, ge=1900, le=9998),
    articulo_id: int | None = Query(None, gt=0),
    pagina: int = Query(1, ge=1),
    limite: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(lector),
):
    q = db.query(ResultadoOperativo)
    if modelo_id:
        q = q.filter_by(modelo_id=modelo_id)
    if alertas:
        q = q.filter_by(alerta=True)
    if articulo_id is not None:
        q = q.filter_by(articulo_id=articulo_id)
    if gestion is not None:
        inicio, fin = limites_gestion(gestion)
        # La gestión pertenece al registro original, aunque se puntúe otro año.
        fuentes = (
            (ResultadoOperativo.movimiento_id, MovimientoKardex),
            (ResultadoOperativo.transferencia_id, TransferenciaArea),
            (ResultadoOperativo.custodia_id, CustodiaExterna),
            (ResultadoOperativo.evento_custodia_id, EventoCustodiaExterna),
        )
        q = q.filter(
            or_(
                *(
                    referencia.in_(
                        select(clase.id).where(
                            clase.registrado_en >= inicio, clase.registrado_en < fin
                        )
                    )
                    for referencia, clase in fuentes
                )
            )
        )
    rs = (
        q.order_by(ResultadoOperativo.creado_en.desc(), ResultadoOperativo.id.desc())
        .offset((pagina - 1) * limite)
        .limit(limite)
        .all()
    )
    nombres = {
        a.id: a.nombre for a in db.query(Activo).filter(Activo.id.in_({r.articulo_id for r in rs}))
    }
    return {
        "total": q.count(),
        "criterio_periodo": "FECHA_REGISTRO_AMERICA_LA_PAZ",
        "filas": [
            dict(
                id=r.id,
                modelo_id=r.modelo_id,
                recurso=r.recurso,
                articulo=nombres[r.articulo_id],
                snapshot=r.snapshot,
                contexto=r.contexto,
                score=r.score,
                alerta=r.alerta,
                creado_en=r.creado_en,
            )
            for r in rs
        ],
    }
