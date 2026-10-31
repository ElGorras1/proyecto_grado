"""Estado de mantenimiento y revisión de inferencias, separados de la evaluación congelada."""

from datetime import UTC, datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.api.deps import require_roles
from app.db.session import get_db
from app.models.activos import Activo
from app.models.auditoria import AuditoriaSistema
from app.models.auditoria_historica import ModeloHistorico, ResultadoHistorico
from app.models.automatizacion_analitica import (
    PoliticaAnalitica,
    ResultadoSeguimiento,
    RevisionSeguimiento,
)
from app.models.kardex import MovimientoKardex
from app.models.usuario import Usuario
from app.schemas.analitica import RevisionAnalitica
from app.services import automatizacion_analitica as servicio
from app.services.datos_analitica import huella, snapshot, leer_corte
from app.services.evaluacion_analitica import diagnosticar

router = APIRouter(prefix="/automatizacion", tags=["Mantenimiento del análisis"])
lector = require_roles("Administrador", "Auditor", "Operador")
administrador = require_roles("Administrador")
revisor = require_roles("Administrador", "Auditor")


def valores(p):
    return {
        k: getattr(p, k)
        for k in (
            "modelo_base_id",
            "habilitada",
            "preparar_candidatos",
            "gestion_hasta",
            "intervalo_segundos",
            "revision_dias",
        )
    }


@router.get("/estado")
def estado(db: Session = Depends(get_db), _=Depends(lector)):
    p = db.get(PoliticaAnalitica, 1)
    if p is None:
        m = servicio.modelo_referencia(db)
        return dict(
            configurada=False,
            habilitada=False,
            modelo_base_id=m.id if m else None,
            huella_politica=None,
        )
    candidato = db.get(ModeloHistorico, p.candidato_id) if p.candidato_id else None
    return dict(
        configurada=True,
        **valores(p),
        huella_politica=huella(valores(p)),
        ultimo_analisis=p.ultimo_analisis,
        ultima_revision=p.ultima_revision,
        proxima_revision=(
            servicio.utc(p.ultima_revision) + timedelta(days=p.revision_dias)
            if p.ultima_revision
            else None
        ),
        ultimo_informe=p.ultimo_informe,
        ultimo_error=p.ultimo_error,
        resultados_seguimiento=db.query(ResultadoSeguimiento)
        .filter_by(modelo_id=p.modelo_base_id)
        .count(),
        candidato=(
            dict(id=candidato.id, estado=candidato.estado, error=candidato.error)
            if candidato
            else None
        ),
        alcance="El análisis usa el modelo conservado. La comprobación periódica puede preparar candidatos; no sustituye automáticamente el modelo en uso ni confirma discrepancias.",
    )


class Configuracion(BaseModel):
    modelo_base_id: UUID
    habilitada: bool = True
    preparar_candidatos: bool = True
    gestion_hasta: int = Field(2025, ge=1900, le=9998)
    intervalo_segundos: int = Field(300, ge=60, le=86400)
    revision_dias: int = Field(30, ge=1, le=365)
    huella_esperada: str | None = Field(None, pattern=r"^[a-f0-9]{64}$")
    motivo: str = Field(min_length=10, max_length=2000)


@router.put("/politica")
def configurar(
    datos: Configuracion,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(administrador),
):
    if len(datos.motivo.strip()) < 10:
        raise HTTPException(422, "Describe el motivo del cambio.")
    p = db.query(PoliticaAnalitica).filter_by(id=1).with_for_update().first()
    if (p and datos.huella_esperada != huella(valores(p))) or (
        p is None and datos.huella_esperada is not None
    ):
        raise HTTPException(409, "La configuración cambió; vuelve a cargarla antes de guardar.")
    m = db.get(ModeloHistorico, str(datos.modelo_base_id))
    if m is None or m.estado != "COMPLETADO":
        raise HTTPException(422, "Selecciona una versión completada y verificada.")
    try:
        servicio.cargar_modelo(m)
    except Exception:
        raise HTTPException(
            422, "El archivo del modelo no está disponible o no coincide con su huella."
        )
    if (
        diagnosticar(m, db.query(ResultadoHistorico).filter_by(modelo_id=m.id).all())["estado"]
        != "CONSISTENTE"
    ):
        raise HTTPException(
            422, "La versión debe superar las comprobaciones técnicas antes de configurarla."
        )
    previo = valores(p) if p else None
    reactivar = p is not None and (
        (not p.habilitada and datos.habilitada)
        or (not p.preparar_candidatos and datos.preparar_candidatos)
    )
    nueva_base = p is None or p.modelo_base_id != m.id or p.gestion_hasta != datos.gestion_hasta
    if p is None:
        p = PoliticaAnalitica(id=1)
        db.add(p)
    for k, v in datos.model_dump(exclude={"huella_esperada", "motivo", "modelo_base_id"}).items():
        setattr(p, k, v)
    p.modelo_base_id = m.id
    if nueva_base:
        p.ultimo_analisis = None
        p.ultima_revision = datetime.now(UTC)
        p.huella_revision = servicio.huella_entrenamiento(
            servicio.elegibles_del_corte(m.corte, p.gestion_hasta)
        )
        p.ultimo_informe = None
        p.ultimo_error = None
        p.candidato_id = None
    elif reactivar:
        p.ultimo_analisis = None
        p.ultima_revision = None
        p.huella_revision = servicio.huella_entrenamiento(
            servicio.elegibles_del_corte(m.corte, p.gestion_hasta)
        )
    db.add(
        AuditoriaSistema(
            usuario_id=usuario.id,
            accion="configurar_automatizacion",
            recurso="politica_analitica",
            recurso_id=1,
            resultado="exito",
            fecha_hora=datetime.now(UTC),
            detalle={"anterior": previo, "nuevo": valores(p), "motivo": datos.motivo.strip()},
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "La configuración cambió durante el guardado; vuelve a cargarla.")
    return estado(db, usuario)


def obtener(db, id):
    r = db.get(ResultadoSeguimiento, id)
    if r is None:
        raise HTTPException(404, "Resultado no encontrado.")
    return r


def actual(db, r):
    fila = (
        db.query(MovimientoKardex, Activo)
        .join(Activo, Activo.id == MovimientoKardex.articulo_id)
        .filter(MovimientoKardex.id == r.movimiento_id)
        .first()
    )
    return snapshot(*fila) if fila else None


@router.get("/seguimiento/{resultado_id}")
def detalle(resultado_id: int, db: Session = Depends(get_db), _=Depends(lector)):
    r = obtener(db, resultado_id)
    m = db.get(ModeloHistorico, r.modelo_id)
    return {
        k: getattr(r, k)
        for k in (
            "id",
            "modelo_id",
            "movimiento_id",
            "articulo_id",
            "gestion",
            "creado_en",
            "snapshot",
            "contexto",
            "score",
            "alerta",
            "estado_revision",
            "revision_numero",
            "etiqueta",
        )
    } | dict(
        umbral=m.umbral,
        datos_cambiaron=actual(db, r) != r.snapshot,
        revisiones=[
            dict(
                id=v.id,
                usuario=u.nombre,
                fecha=v.creado_en,
                estado=v.estado,
                etiqueta=v.etiqueta,
                motivo=v.motivo,
            )
            for v, u in db.query(RevisionSeguimiento, Usuario)
            .join(Usuario, Usuario.id == RevisionSeguimiento.usuario_id)
            .filter(RevisionSeguimiento.resultado_id == r.id)
            .order_by(RevisionSeguimiento.id)
        ],
    )


@router.post("/seguimiento/{resultado_id}/revision")
def revisar(
    resultado_id: int,
    datos: RevisionAnalitica,
    db: Session = Depends(get_db),
    usuario=Depends(revisor),
):
    r = obtener(db, resultado_id)
    f = actual(db, r)
    p = db.get(PoliticaAnalitica, 1)
    elegibles = {
        f["id"]
        for f in servicio.elegibles_del_corte(leer_corte(db), p.gestion_hasta if p else 2025)
    }
    if (
        f is None
        or f != r.snapshot
        or r.movimiento_id not in elegibles
        or (p and p.modelo_base_id != r.modelo_id)
    ):
        raise HTTPException(
            409, "La evidencia cambió o requiere revisión documental; espera al nuevo análisis."
        )
    if datos.estado == "JUSTIFICADO" and datos.etiqueta != "LEGITIMO":
        raise HTTPException(422, "Justificado requiere la conclusión Legítimo.")
    if datos.estado == "CERRADO" and datos.etiqueta == "NO_CONCLUYENTE":
        raise HTTPException(
            422, "Un caso no concluyente debe permanecer en revisión o seguimiento."
        )
    previo = r.estado_revision
    n = (
        db.query(ResultadoSeguimiento)
        .filter_by(id=r.id, revision_numero=datos.revision_esperada)
        .update(
            dict(
                estado_revision=datos.estado,
                etiqueta=datos.etiqueta,
                revision_numero=datos.revision_esperada + 1,
            ),
            synchronize_session=False,
        )
    )
    if n != 1:
        raise HTTPException(409, "Otra persona actualizó la revisión; vuelve a cargarla.")
    db.add(
        RevisionSeguimiento(
            resultado_id=r.id,
            usuario_id=usuario.id,
            creado_en=datetime.now(UTC),
            anterior=previo,
            estado=datos.estado,
            etiqueta=datos.etiqueta,
            motivo=datos.motivo,
        )
    )
    db.add(
        AuditoriaSistema(
            usuario_id=usuario.id,
            accion="revisar_seguimiento_automatico",
            recurso="resultado_seguimiento",
            recurso_id=r.id,
            resultado="exito",
            fecha_hora=datetime.now(UTC),
            detalle=datos.model_dump(),
        )
    )
    db.commit()
    db.expire_all()
    return detalle(resultado_id, db, usuario)
