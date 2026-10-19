"""Rectificaciones y ajustes mediante asientos nuevos, autorizados y auditables."""
import hashlib
import json
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.config import settings
from app.db.session import get_db
from app.models.activos import Activo
from app.models.inventario import AperturaInventario
from app.models.kardex import MovimientoKardex
from app.models.usuario import Usuario
from app.services.control_alertas import registrar_caso
from app.schemas.kardex import MovimientoKardexOut
from app.services.inventario import (
    auditar, bloquear_apertura, cambiar_existencia_area, verificar_distribucion,
    cantidad_efectiva_movimiento, cantidad_devuelta_efectiva,
)
from app.services.control_movimientos import evaluar_movimiento, parametros_control, evaluar_ubicacion, stock_ubicacion


router = APIRouter(prefix="/kardex", tags=["Ajustes operativos"])


class EvidenciaAjuste(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    solicitud_id: UUID
    motivo: str = Field(min_length=10, max_length=2000)
    referencia_documento: str = Field(min_length=3, max_length=200)


class RectificacionCrear(EvidenciaAjuste):
    cantidad_corregida: int = Field(strict=True, ge=0, le=2147483647)


class AjusteCrear(EvidenciaAjuste):
    direccion: Literal["ingreso", "salida"]
    cantidad: int = Field(strict=True, gt=0, le=2147483647)
    area_id: int | None = Field(default=None, gt=0)
    encargado_id: int = Field(gt=0)


def huella(payload: BaseModel, usuario: Usuario, *, articulo_id: int,
           origen_id: int | None = None) -> str:
    contenido = payload.model_dump(mode="json") | {
        "articulo_id": articulo_id, "origen_id": origen_id, "registrado_por": usuario.id,
    }
    return hashlib.sha256(json.dumps(contenido, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode()).hexdigest()


def previo(db: Session, solicitud_id: str, firma: str):
    fila = db.query(MovimientoKardex).filter_by(solicitud_id=solicitud_id).first()
    if fila is None:
        return None
    if fila.solicitud_huella != firma:
        raise HTTPException(409, "Esta clave ya corresponde a otra operación.")
    return fila


def asiento(db: Session, *, articulo_id: int, usuario: Usuario,
            encargado: Usuario, solicitud_id: str, firma: str,
            delta: int, saldo: int, area_id: int | None,
            motivo: str, documento: str, tipo: str,
            alertas: list[dict],
            original: MovimientoKardex | None = None,
            cantidad_anterior: int | None = None,
            cantidad_corregida: int | None = None) -> MovimientoKardex:
    ahora = datetime.now(UTC)
    fila = MovimientoKardex(
        articulo_id=articulo_id,
        fecha_movimiento=ahora.astimezone(ZoneInfo("America/La_Paz")).date(),
        detalle=f"{tipo}: {motivo}", observaciones=motivo,
        ingresos=delta if delta > 0 else None,
        salidas=-delta if delta < 0 else None,
        saldo_registrado=saldo, saldo_calculado=saldo,
        tiene_error_saldo=False, requiere_auditoria_nodo=False,
        requiere_auditoria_referencia=False,
        nodo_grafo="Ajuste Operativo", area_estado="NO_APLICA",
        referencia_estado="PRESENTE", estado="ACTIVO",
        usuario_operador=usuario.nombre, usuario_registrador_id=usuario.id,
        encargado_id=encargado.id, encargado_nombre=encargado.nombre,
        autorizado_por_id=usuario.id, registrado_en=ahora, ocurrido_en=ahora,
        solicitud_id=solicitud_id, solicitud_huella=firma,
        tipo_operacion=tipo, area_operativa_id=area_id,
        referencia_documento=documento,
        corrige_movimiento_id=original.id if original else None,
        cantidad_anterior=cantidad_anterior,
        cantidad_corregida=cantidad_corregida,
        motivo_correccion=motivo,
        alertas_control=alertas or None,
        justificacion_alertas=motivo if alertas else None,
    )
    db.add(fila)
    db.flush()
    registrar_caso(db, fila, "MOVIMIENTO")
    return fila


def respuesta(db: Session, solicitud_id: str, firma: str):
    existente = previo(db, solicitud_id, firma)
    if existente is not None:
        return existente
    return None


def alertas_ajuste(delta: int, saldo: int, db, apertura, area_id) -> list[dict]:
    alertas = evaluar_movimiento(
        tipo="ingreso" if delta > 0 else "salida",
        cantidad=abs(delta), saldo=saldo,
        fecha_local=datetime.now(ZoneInfo("America/La_Paz")),
        cantidades_previas=[], **parametros_control(),
    )
    ubicacion = stock_ubicacion(db, apertura, area_id)
    if delta < 0 and ubicacion < saldo:
        alertas += evaluar_ubicacion(cantidad=abs(delta), saldo=ubicacion,
            codigo_total="AGOTA_SIN_UBICACION" if area_id is None else "AGOTA_AREA",
            codigo_mayoria="AJUSTE_MAYORITARIO_UBICACION", etiqueta="saldo sin ubicación confirmada" if area_id is None else "el área del ajuste",
            porcentaje=settings.CONTROL_PORCENTAJE_MAYORITARIO, minimo=settings.CONTROL_STOCK_MINIMO_MAYORITARIO)
    return alertas


@router.post("/movimiento-actual/{movimiento_id}/corregir", response_model=MovimientoKardexOut)
def corregir_movimiento(
    movimiento_id: int, payload: RectificacionCrear, request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("Administrador")),
):
    original = db.get(MovimientoKardex, movimiento_id)
    if original is None:
        raise HTTPException(404, "Movimiento no encontrado")
    firma = huella(payload, usuario, articulo_id=original.articulo_id, origen_id=movimiento_id)
    solicitud_id = str(payload.solicitud_id)
    anterior = respuesta(db, solicitud_id, firma)
    if anterior is not None:
        return anterior
    apertura = bloquear_apertura(db, original.articulo_id)
    db.refresh(original)
    anterior = respuesta(db, solicitud_id, firma)
    if anterior is not None:
        db.rollback()
        return anterior
    if (original.lote_id is not None or original.id <= apertura.ultimo_moderno_id
            or original.estado != "ACTIVO" or original.corrige_movimiento_id is not None
            or original.tipo_operacion in ("Ajuste de Conciliación Inicial",
                                           "Ajuste operativo", "Rectificación operativa")):
        raise HTTPException(409, "Selecciona una entrada, salida o devolución activa posterior al corte.")
    cantidad_original = (original.ingresos or 0) + (original.salidas or 0)
    if cantidad_original <= 0 or bool(original.ingresos) == bool(original.salidas):
        raise HTTPException(409, "La operación original no tiene una cantidad corregible.")
    cantidad_anterior = cantidad_efectiva_movimiento(db, original)
    if payload.cantidad_corregida == cantidad_anterior:
        raise HTTPException(409, "La cantidad corregida debe ser diferente de la vigente.")
    if original.movimiento_origen_id is not None:
        entrega = db.get(MovimientoKardex, original.movimiento_origen_id)
        if (original.tipo_operacion != "Devolución" or not original.ingresos
                or entrega is None or entrega.estado != "ACTIVO"):
            raise HTTPException(409, "La devolución vinculada no se puede rectificar automáticamente.")
        limite = (cantidad_efectiva_movimiento(db, entrega)
                  - cantidad_devuelta_efectiva(db, entrega.id,
                                               excluir_id=original.id))
        if payload.cantidad_corregida > limite:
            raise HTTPException(409, "La rectificación excedería las unidades de la venta o donación original.")
    elif original.salidas and original.tipo_operacion in ("Ventas", "Obsequios y Donaciones"):
        devuelto = cantidad_devuelta_efectiva(db, original.id)
        if payload.cantidad_corregida < devuelto:
            raise HTTPException(409, "La cantidad corregida no puede ser menor que las devoluciones vigentes.")
    delta = (payload.cantidad_corregida - cantidad_anterior) * (
        1 if original.ingresos else -1)
    nuevo_total = apertura.cantidad_actual + delta
    if not 0 <= nuevo_total <= 2147483647:
        raise HTTPException(409, "La rectificación dejaría un total institucional inválido.")
    alertas = alertas_ajuste(delta, apertura.cantidad_actual, db, apertura, original.area_operativa_id)
    cambiar_existencia_area(db, apertura, original.area_operativa_id, delta,
                            exigir_area_activa=False)
    apertura.cantidad_actual = nuevo_total
    try:
        fila = asiento(db, articulo_id=original.articulo_id, usuario=usuario,
            encargado=usuario, solicitud_id=solicitud_id, firma=firma,
            delta=delta, saldo=nuevo_total, area_id=original.area_operativa_id,
            motivo=payload.motivo, documento=payload.referencia_documento,
            alertas=alertas,
            tipo="Rectificación operativa", original=original,
            cantidad_anterior=cantidad_anterior,
            cantidad_corregida=payload.cantidad_corregida)
        verificar_distribucion(db, apertura)
    except IntegrityError:
        db.rollback()
        existente = respuesta(db, solicitud_id, firma)
        if existente is not None:
            return existente
        raise
    auditar(db, usuario, request, "rectificar_movimiento_operativo",
            "movimientos_kardex", fila.id,
            {"original_id": original.id, "articulo_id": original.articulo_id,
             "cantidad_anterior": cantidad_anterior,
             "cantidad_corregida": payload.cantidad_corregida,
             "delta": delta, "motivo": payload.motivo,
             "documento": payload.referencia_documento,
             "autorizado_por_id": usuario.id,
             "alertas_control": [a["codigo"] for a in alertas]})
    db.commit()
    db.refresh(fila)
    return fila


@router.post("/articulos/{articulo_id}/ajustes-operativos", response_model=MovimientoKardexOut)
def registrar_ajuste(
    articulo_id: int, payload: AjusteCrear, request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("Administrador")),
):
    if db.get(Activo, articulo_id) is None:
        raise HTTPException(404, "Artículo no encontrado")
    firma = huella(payload, usuario, articulo_id=articulo_id)
    solicitud_id = str(payload.solicitud_id)
    anterior = respuesta(db, solicitud_id, firma)
    if anterior is not None:
        return anterior
    encargado = db.get(Usuario, payload.encargado_id)
    if encargado is None or encargado.estado != "activo":
        raise HTTPException(422, "Selecciona un encargado activo.")
    apertura = bloquear_apertura(db, articulo_id)
    anterior = respuesta(db, solicitud_id, firma)
    if anterior is not None:
        db.rollback()
        return anterior
    delta = payload.cantidad if payload.direccion == "ingreso" else -payload.cantidad
    nuevo_total = apertura.cantidad_actual + delta
    if not 0 <= nuevo_total <= 2147483647:
        raise HTTPException(409, "El ajuste dejaría un total institucional inválido.")
    alertas = alertas_ajuste(delta, apertura.cantidad_actual, db, apertura, payload.area_id)
    cambiar_existencia_area(db, apertura, payload.area_id, delta)
    apertura.cantidad_actual = nuevo_total
    try:
        fila = asiento(db, articulo_id=articulo_id, usuario=usuario,
            encargado=encargado, solicitud_id=solicitud_id, firma=firma,
            delta=delta, saldo=nuevo_total, area_id=payload.area_id,
            motivo=payload.motivo, documento=payload.referencia_documento,
            alertas=alertas,
            tipo="Ajuste operativo")
        verificar_distribucion(db, apertura)
    except IntegrityError:
        db.rollback()
        existente = respuesta(db, solicitud_id, firma)
        if existente is not None:
            return existente
        raise
    auditar(db, usuario, request, "ajustar_inventario_operativo",
            "movimientos_kardex", fila.id,
            {"articulo_id": articulo_id, "direccion": payload.direccion,
             "cantidad": payload.cantidad, "area_id": payload.area_id,
             "motivo": payload.motivo, "documento": payload.referencia_documento,
             "encargado_id": encargado.id, "autorizado_por_id": usuario.id,
             "alertas_control": [a["codigo"] for a in alertas]})
    db.commit()
    db.refresh(fila)
    return fila
