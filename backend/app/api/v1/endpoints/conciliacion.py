"""Conciliación física del saldo inicial antes de los movimientos operativos."""
from datetime import UTC, date, datetime
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.activos import Activo, Existencia
from app.services.cierre_documental import fuente_cierre
from app.models.area import Area
from app.models.inventario import AperturaInventario, ConciliacionInicial, CustodiaExterna
from app.models.inventario import TransferenciaArea
from app.models.rectificacion_logistica import RectificacionLogistica
from app.models.kardex import MovimientoKardex
from app.models.usuario import Usuario
from app.services.clasificador_nodos import AREA_NO_APLICA, REFERENCIA_PRESENTE
from app.services.inventario import (
    asegurar_apertura_desde_kardex, auditar, base_kardex_dict,
    distribucion_dict, verificar_distribucion,
)

router = APIRouter(prefix="/kardex/articulos", tags=["Conciliación inicial"])
NOMBRE_AJUSTE = "Ajuste de Conciliación Inicial"


class ConteoArea(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    area_id: int = Field(gt=0)
    cantidad: int = Field(strict=True, ge=0, le=2147483647)


class ConciliacionCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    fecha_conteo: date
    areas: list[ConteoArea] = Field(min_length=1, max_length=100)
    encargado_id: int = Field(gt=0)
    referencia_documento: str = Field(min_length=3, max_length=200)
    justificacion: str = Field(min_length=10, max_length=2000)
    alcance_total: Literal[True]
    conteo_verificado: Literal[True]

    @model_validator(mode="after")
    def validar_areas(self):
        ids = [a.area_id for a in self.areas]
        if len(ids) != len(set(ids)):
            raise ValueError("Cada área debe aparecer una sola vez")
        if sum(a.cantidad for a in self.areas) > 2147483647:
            raise ValueError("El conteo supera la cantidad máxima admitida")
        return self


def registro_dict(row: ConciliacionInicial) -> dict:
    return {campo: getattr(row, campo) for campo in (
        "articulo_id", "cantidad_base", "cantidad_fisica", "diferencia",
        "fecha_conteo", "distribucion_anterior", "areas", "referencia_documento", "justificacion",
        "encargado_id", "registrado_por", "registrado_en", "origen_base",
        "movimiento_historico_id", "ajuste_movimiento_id",
    )}


def impedimento_inicial(db: Session, apertura: AperturaInventario) -> str | None:
    if db.query(TransferenciaArea.id).filter_by(articulo_id=apertura.articulo_id).first():
        return "Ya hubo transferencias posteriores al corte; corresponde un conteo posterior y ajuste autorizado, no una conciliación inicial."
    if db.query(RectificacionLogistica.id).filter_by(articulo_id=apertura.articulo_id).first():
        return "Ya existen rectificaciones posteriores al corte; conserva su trazabilidad y registra un ajuste autorizado."
    if db.query(CustodiaExterna.id).filter_by(articulo_id=apertura.articulo_id).first():
        return "Ya hubo una entrega en custodia externa; corresponde un ajuste operativo, no una conciliación inicial."
    if db.query(MovimientoKardex.id).filter(
        MovimientoKardex.articulo_id == apertura.articulo_id,
        MovimientoKardex.lote_id.is_(None),
        MovimientoKardex.id > apertura.ultimo_moderno_id,
    ).first():
        return "Ya existen movimientos posteriores al corte; corresponde un ajuste operativo, no una conciliación inicial."
    return None


@router.get("/{articulo_id}/conciliacion-inicial")
def consultar_conciliacion(
    articulo_id: int, db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    if db.get(Activo, articulo_id) is None:
        raise HTTPException(404, "Artículo no encontrado")
    registrada = db.get(ConciliacionInicial, articulo_id)
    if registrada:
        return {"estado": "REGISTRADA", "motivo": None,
                "registro": registro_dict(registrada)}
    apertura = db.get(AperturaInventario, articulo_id)
    if apertura:
        motivo = impedimento_inicial(db, apertura)
        base = apertura.cantidad_actual
    else:
        fuente = fuente_cierre(db, articulo_id)
        cierre = fuente.cierre if fuente else None
        base_doc = base_kardex_dict(cierre, fuente)
        motivo = (base_doc["motivo_bloqueo"] if base_doc else
                  "No hay cierre histórico; primero aprueba una apertura por conteo físico.")
        base = base_doc["saldo"] if base_doc else None
    return {"estado": "NO_DISPONIBLE" if motivo else "DISPONIBLE",
            "motivo": motivo, "cantidad_base": base, "registro": None}


@router.post("/{articulo_id}/conciliacion-inicial")
def registrar_conciliacion(
    articulo_id: int, payload: ConciliacionCrear, request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("Administrador")),
):
    """Fija un conteo total por áreas y un ajuste explícito, en una transacción."""
    hoy_local = datetime.now(ZoneInfo("America/La_Paz")).date()
    if payload.fecha_conteo > hoy_local:
        raise HTTPException(422, "La fecha del conteo no puede estar en el futuro.")
    encargado = db.query(Usuario).filter_by(id=payload.encargado_id,
                                            estado="activo").first()
    if encargado is None:
        raise HTTPException(422, "Selecciona un encargado activo.")
    areas = {a.id: a for a in db.query(Area).filter(
        Area.id.in_([item.area_id for item in payload.areas]),
        Area.estado == "activo",
    ).all()}
    if len(areas) != len(payload.areas):
        raise HTTPException(422, "El conteo contiene un área inexistente o inactiva.")

    apertura = asegurar_apertura_desde_kardex(db, articulo_id, usuario, request)
    areas = {a.id: a for a in db.query(Area).filter(
        Area.id.in_([item.area_id for item in payload.areas]), Area.estado == "activo",
    ).order_by(Area.id).populate_existing().with_for_update(read=True).all()}
    if len(areas) != len(payload.areas):
        raise HTTPException(422, "El área cambió durante el conteo; revisa su vigencia.")
    if db.get(ConciliacionInicial, articulo_id):
        raise HTTPException(409, "Este artículo ya tiene una conciliación inicial registrada.")
    motivo = impedimento_inicial(db, apertura)
    if motivo:
        raise HTTPException(409, motivo)

    base = apertura.cantidad_actual
    total = sum(item.cantidad for item in payload.areas)
    diferencia = total - base
    ahora = datetime.now(UTC)
    distribucion_anterior = distribucion_dict(db, articulo_id, apertura)
    ajuste = None
    if diferencia:
        ajuste = MovimientoKardex(
            articulo_id=articulo_id, fecha_movimiento=payload.fecha_conteo,
            detalle="Ajuste documentado por conciliación física inicial",
            ingresos=diferencia if diferencia > 0 else None,
            salidas=-diferencia if diferencia < 0 else None,
            saldo_registrado=total, saldo_calculado=total,
            tiene_error_saldo=False, requiere_auditoria_nodo=False,
            requiere_auditoria_referencia=False,
            nodo_grafo=NOMBRE_AJUSTE, area_estado=AREA_NO_APLICA,
            referencia_estado=REFERENCIA_PRESENTE,
            observaciones=payload.justificacion, estado="ACTIVO",
            usuario_operador=usuario.nombre, usuario_registrador_id=usuario.id,
            encargado_id=encargado.id, encargado_nombre=encargado.nombre,
            registrado_en=ahora, tipo_operacion=NOMBRE_AJUSTE,
            referencia_documento=payload.referencia_documento,
        )
        db.add(ajuste)
        db.flush()

    apertura.cantidad_actual = total
    apertura.cantidad_sin_ubicacion = 0
    for existencia in db.query(Existencia).filter_by(activo_id=articulo_id).with_for_update().all():
        db.delete(existencia)
    db.flush()
    detalle_areas = []
    for item in payload.areas:
        detalle_areas.append({"area_id": item.area_id, "area": areas[item.area_id].nombre,
                              "cantidad": item.cantidad})
        if item.cantidad:
            db.add(Existencia(activo_id=articulo_id, area_id=item.area_id,
                              cantidad=item.cantidad, estado="activo"))
    verificar_distribucion(db, apertura)
    registro = ConciliacionInicial(
        articulo_id=articulo_id, cantidad_base=base, cantidad_fisica=total,
        diferencia=diferencia, fecha_conteo=payload.fecha_conteo,
        distribucion_anterior=distribucion_anterior,
        areas=detalle_areas, referencia_documento=payload.referencia_documento,
        justificacion=payload.justificacion, encargado_id=encargado.id,
        registrado_por=usuario.id, registrado_en=ahora,
        origen_base=apertura.origen,
        movimiento_historico_id=apertura.movimiento_historico_id,
        ajuste_movimiento_id=ajuste.id if ajuste else None,
    )
    db.add(registro)
    auditar(db, usuario, request, "conciliar_inventario_inicial", "conciliacion_inicial",
            articulo_id, {"base": base, "conteo": total, "diferencia": diferencia,
                          "distribucion_anterior": distribucion_anterior,
                          "areas": detalle_areas, "encargado_id": encargado.id,
                          "referencia_documento": payload.referencia_documento,
                          "justificacion": payload.justificacion,
                          "ajuste_movimiento_id": ajuste.id if ajuste else None})
    db.commit()
    return {"estado": "REGISTRADA", "registro": registro_dict(registro),
            "distribucion": distribucion_dict(db, articulo_id, apertura)}
