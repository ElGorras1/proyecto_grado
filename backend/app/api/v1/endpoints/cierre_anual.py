"""Cierre digital anual con corte revisable, reintento seguro y reapertura explícita."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.v1.endpoints.analitica_operativa import bloqueo
from app.db.session import get_db
from app.models.activos import Activo
from app.models.cierre_anual import CierreAnual
from app.models.control_alertas import CasoControl
from app.models.inventario import AperturaInventario
from app.services import cierre_anual as servicio
from app.services.datos_analitica import huella
from app.services.inventario import auditar

router = APIRouter(prefix="/cierres-anuales", tags=["Cierres anuales digitales"])
lector = require_roles("Administrador", "Auditor", "Operador")
admin = require_roles("Administrador")


class Cerrar(BaseModel):
    solicitud_id: UUID
    huella_esperada: str = Field(pattern=r"^[a-f0-9]{64}$")
    documento: str = Field(min_length=3, max_length=200)
    motivo: str = Field(min_length=10, max_length=2000)
    balance_revisado: bool

    @field_validator("documento", "motivo")
    @classmethod
    def limpiar(cls, v):
        v = v.strip()
        if len(v) < 3:
            raise ValueError("La evidencia no puede estar vacía.")
        return v


class Reabrir(BaseModel):
    motivo: str = Field(min_length=10, max_length=2000)

    @field_validator("motivo")
    @classmethod
    def limpiar(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Explica el motivo de la reapertura.")
        return v.strip()


def publico(c):
    return {
        k: getattr(c, k)
        for k in (
            "id",
            "gestion",
            "version",
            "estado",
            "snapshot",
            "huella",
            "creado_en",
            "usuario_id",
            "documento",
            "motivo",
            "reabierto_por",
            "reabierto_en",
            "motivo_reapertura",
        )
    }


@router.get("")
def listar(
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(lector),
):
    q = db.query(CierreAnual)
    return {
        "total": q.count(),
        "filas": [
            publico(c)
            for c in q.order_by(CierreAnual.gestion.desc(), CierreAnual.version.desc())
            .offset((pagina - 1) * limite)
            .limit(limite)
        ],
    }


@router.get("/{gestion}/vista-previa")
def preview(gestion: int, db: Session = Depends(get_db), _=Depends(lector)):
    if gestion < 1900 or gestion > 9998:
        raise HTTPException(422, "Gestión inválida")
    return servicio.reconstruir(db, gestion)


@router.post("/{gestion}", status_code=201)
def cerrar(
    gestion: int,
    payload: Cerrar,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(admin),
):
    if gestion < 1900 or gestion > 9998:
        raise HTTPException(422, "Gestión inválida")
    if not payload.balance_revisado or len(payload.motivo.strip()) < 10:
        raise HTTPException(422, "Revisa el balance y documenta el motivo antes de cerrar.")
    identidad = huella(
        payload.model_dump(mode="json") | {"gestion": gestion, "usuario_id": usuario.id}
    )
    with bloqueo(db, 681940263):
        previo = db.query(CierreAnual).filter_by(solicitud_id=str(payload.solicitud_id)).first()
        if previo:
            if previo.solicitud_huella != identidad:
                raise HTTPException(409, "La solicitud ya se usó con otros datos.")
            return publico(previo)
        if db.query(CierreAnual.id).filter_by(gestion_activa=gestion).first():
            raise HTTPException(409, "Esta gestión ya tiene un cierre vigente.")
        # Aperturas nuevas toman Activo; transferencias/custodias/ajustes toman
        # AperturaInventario. Proteger ambos, en el mismo orden que los escritores.
        db.query(Activo).order_by(Activo.id).with_for_update().all()
        db.query(AperturaInventario).order_by(
            AperturaInventario.articulo_id
        ).populate_existing().with_for_update().all()
        db.query(CasoControl).order_by(CasoControl.id).with_for_update().all()
        actual = servicio.reconstruir(db, gestion)
        if not actual["puede_cerrar"]:
            raise HTTPException(
                409,
                {
                    "mensaje": "Hay impedimentos para cerrar.",
                    "impedimentos": actual["impedimentos"],
                },
            )
        if actual["huella"] != payload.huella_esperada:
            raise HTTPException(409, "El balance cambió; vuelve a revisar la vista previa.")
        version = (
            db.query(func.max(CierreAnual.version)).filter_by(gestion=gestion).scalar() or 0
        ) + 1
        c = CierreAnual(
            solicitud_id=str(payload.solicitud_id),
            solicitud_huella=identidad,
            gestion=gestion,
            gestion_activa=gestion,
            version=version,
            estado="CERRADO",
            snapshot=actual["snapshot"],
            huella=actual["huella"],
            usuario_id=usuario.id,
            creado_en=servicio.ahora(),
            documento=payload.documento,
            motivo=payload.motivo.strip(),
        )
        db.add(c)
        db.flush()
        auditar(
            db,
            usuario,
            request,
            "cerrar_gestion_digital",
            "cierre_anual",
            c.id,
            {"gestion": gestion, "version": version, "huella": c.huella},
        )
        db.commit()
        return publico(c)


@router.post("/registro/{id}/reabrir")
def reabrir(
    id: int,
    payload: Reabrir,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(admin),
):
    with bloqueo(db, 681940263):
        c = db.query(CierreAnual).filter_by(id=id).with_for_update().first()
        if not c:
            raise HTTPException(404, "Cierre no encontrado")
        if c.estado == "REABIERTO":
            return publico(c)
        c.estado, c.gestion_activa = "REABIERTO", None
        c.reabierto_por, c.reabierto_en, c.motivo_reapertura = (
            usuario.id,
            servicio.ahora(),
            payload.motivo,
        )
        auditar(
            db,
            usuario,
            request,
            "reabrir_gestion_digital",
            "cierre_anual",
            c.id,
            {"gestion": c.gestion, "version": c.version, "motivo": payload.motivo},
        )
        db.commit()
        return publico(c)
