"""Entregas a ferias/consignatarios, ventas y retornos con saldo institucional íntegro."""
import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.activos import Activo
from app.models.activos import Existencia
from app.models.area import Area
from app.models.inventario import AperturaInventario, CustodiaExterna, EventoCustodiaExterna
from app.models.usuario import Usuario
from app.services.control_alertas import registrar_caso
from app.services.inventario import (
    auditar, bloquear_apertura, cambiar_existencia_area, distribucion_dict,
    verificar_distribucion,
)
from app.services.control_movimientos import (
    evaluar_movimiento, confirmar_alertas, parametros_control, evaluar_ubicacion, aviso_repeticion,
)
from app.core.config import settings


router = APIRouter(prefix="/kardex/articulos", tags=["Custodia externa"])


class EntregaCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    solicitud_id: uuid.UUID
    tipo: Literal["FERIA", "CONSIGNACION"]
    area_origen_id: int = Field(gt=0)
    receptor_nombre: str = Field(min_length=3, max_length=200)
    receptor_tipo: Literal["PERSONA", "INSTITUCION"]
    ubicacion_externa: str = Field(min_length=3, max_length=200)
    ciudad: str | None = Field(default=None, max_length=100)
    cantidad: int = Field(strict=True, gt=0, le=2147483647)
    encargado_id: int = Field(gt=0)
    fecha_operacion: AwareDatetime | None = None
    referencia_documento: str = Field(min_length=3, max_length=200)
    observaciones: str = Field(default="", max_length=1000)
    confirmacion_alertas: str | None = Field(default=None, min_length=64, max_length=64)
    motivo_alertas: str = Field(default="", max_length=1000)


class EventoCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    solicitud_id: uuid.UUID
    tipo: Literal["VENTA", "RETORNO"]
    cantidad: int = Field(strict=True, gt=0, le=2147483647)
    area_destino_id: int | None = Field(default=None, gt=0)
    comprador: str | None = Field(default=None, max_length=200)
    encargado_id: int = Field(gt=0)
    fecha_operacion: AwareDatetime | None = None
    referencia_documento: str = Field(min_length=3, max_length=200)
    observaciones: str = Field(default="", max_length=1000)
    confirmacion_alertas: str | None = Field(default=None, min_length=64, max_length=64)
    motivo_alertas: str = Field(default="", max_length=1000)


def huella(payload: BaseModel, articulo_id: int, usuario_id: int,
           custodia_id: int | None = None) -> str:
    contenido = payload.model_dump(mode="json", exclude={
        "confirmacion_alertas", "motivo_alertas"}) | {
        "articulo_id": articulo_id, "registrado_por": usuario_id,
        "custodia_id": custodia_id,
    }
    return hashlib.sha256(json.dumps(contenido, sort_keys=True,
        ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def fecha_valida(fecha: AwareDatetime | None, ahora: datetime, inicio: datetime) -> datetime:
    ocurrio = fecha.astimezone(UTC) if fecha else ahora
    if ocurrio > ahora + timedelta(minutes=5):
        raise HTTPException(422, "La fecha de la operación no puede estar en el futuro.")
    if inicio.tzinfo is None:  # SQLite en pruebas.
        inicio = inicio.replace(tzinfo=UTC)
    if ocurrio < inicio:
        raise HTTPException(409, "La operación ocurrió antes de la entrega o del corte de apertura.")
    return ocurrio


def encargado_activo(db: Session, encargado_id: int) -> Usuario:
    encargado = db.get(Usuario, encargado_id)
    if encargado is None or encargado.estado != "activo":
        raise HTTPException(422, "Selecciona un encargado activo.")
    return encargado


def entrega_dict(db: Session, fila: CustodiaExterna) -> dict:
    area = db.get(Area, fila.area_origen_id)
    return {campo: getattr(fila, campo) for campo in (
        "id", "solicitud_id", "articulo_id", "tipo", "area_origen_id",
        "receptor_nombre", "receptor_tipo", "ubicacion_externa", "ciudad",
        "cantidad_entregada", "cantidad_fuera", "cantidad_vendida",
        "cantidad_devuelta", "total_institucional_entrega", "encargado_id",
        "registrado_por", "ocurrido_en", "registrado_en", "referencia_documento",
        "observaciones",
        "alertas_control", "justificacion_alertas",
    )} | {"area_origen": area.nombre if area else None,
         "estado": "ABIERTA" if fila.cantidad_fuera else "CERRADA"}


def evento_dict(db: Session, fila: EventoCustodiaExterna) -> dict:
    area = db.get(Area, fila.area_destino_id) if fila.area_destino_id else None
    return {campo: getattr(fila, campo) for campo in (
        "id", "solicitud_id", "custodia_id", "articulo_id", "tipo", "cantidad",
        "area_destino_id", "comprador", "encargado_id", "registrado_por",
        "ocurrido_en", "registrado_en", "referencia_documento", "observaciones",
        "total_institucional_despues", "cantidad_fuera_despues",
        "alertas_control", "justificacion_alertas",
    )} | {"area_destino": area.nombre if area else None}


@router.get("/{articulo_id}/custodias-externas")
def listar_custodias(
    articulo_id: int, db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    if db.get(Activo, articulo_id) is None:
        raise HTTPException(404, "Artículo no encontrado")
    entregas = db.query(CustodiaExterna).filter_by(articulo_id=articulo_id).order_by(
        CustodiaExterna.id.desc()).all()
    eventos = db.query(EventoCustodiaExterna).filter_by(articulo_id=articulo_id).order_by(
        EventoCustodiaExterna.id).all()
    por_entrega = {e.id: [] for e in entregas}
    for evento in eventos:
        por_entrega[evento.custodia_id].append(evento_dict(db, evento))
    return [{**entrega_dict(db, entrega), "eventos": por_entrega[entrega.id]}
            for entrega in entregas]


@router.post("/{articulo_id}/custodias-externas")
def entregar_custodia(
    articulo_id: int, payload: EntregaCrear, request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    solicitud_id = str(payload.solicitud_id)
    firma = huella(payload, articulo_id, usuario.id)

    def respuesta_previa():
        previa = db.query(CustodiaExterna).filter_by(solicitud_id=solicitud_id).first()
        if previa is None:
            return None
        if previa.solicitud_huella != firma:
            raise HTTPException(409, "Esta clave ya pertenece a otra entrega externa.")
        return {"registro": entrega_dict(db, previa),
                "distribucion": distribucion_dict(db, articulo_id,
                    db.get(AperturaInventario, articulo_id))}

    previa = respuesta_previa()
    if previa is not None:
        return previa
    if payload.tipo == "FERIA" and not (payload.ciudad or "").strip():
        raise HTTPException(422, "La entrega a feria requiere indicar la ciudad.")
    encargado_activo(db, payload.encargado_id)
    area = db.get(Area, payload.area_origen_id)
    if area is None or area.estado != "activo":
        raise HTTPException(422, "Selecciona un área de origen activa.")

    ahora = datetime.now(UTC)
    apertura = bloquear_apertura(db, articulo_id)
    previa = respuesta_previa()
    if previa is not None:
        db.rollback()
        return previa
    ocurrio = fecha_valida(payload.fecha_operacion, ahora, apertura.aprobado_en)
    origen_stock = db.query(Existencia).filter_by(
        activo_id=articulo_id, area_id=area.id).with_for_update().first()
    stock_area = int(origen_stock.cantidad) if origen_stock else 0
    if payload.cantidad > stock_area:
        db.rollback()
        raise HTTPException(409, "Stock insuficiente en el área que entrega.")
    comparables = db.query(CustodiaExterna).filter_by(
        articulo_id=articulo_id, tipo=payload.tipo, area_origen_id=area.id)
    cantidades_previas = [c.cantidad_entregada for c in comparables.order_by(CustodiaExterna.id.desc()).limit(20)]
    alertas = evaluar_movimiento(
        tipo="ingreso", cantidad=payload.cantidad, saldo=stock_area,
        fecha_local=ahora.astimezone(ZoneInfo("America/La_Paz")),
        cantidades_previas=cantidades_previas,
        fecha_operacion_local=ocurrio.astimezone(ZoneInfo("America/La_Paz")) if payload.fecha_operacion else None, **parametros_control(),
    )
    alertas += evaluar_ubicacion(cantidad=payload.cantidad, saldo=stock_area,
        codigo_total="AGOTA_AREA_POR_CUSTODIA", codigo_mayoria="ENTREGA_MAYORITARIA_AREA",
        etiqueta="el área de origen al entregar a custodia", porcentaje=settings.CONTROL_PORCENTAJE_MAYORITARIO,
        minimo=settings.CONTROL_STOCK_MINIMO_MAYORITARIO)
    recientes = comparables.filter(CustodiaExterna.registrado_en >= ahora - timedelta(
        minutes=settings.CONTROL_REPETICION_MINUTOS)).all()
    alertas += aviso_repeticion([dict(id=c.id, cantidad=c.cantidad_entregada, documento=c.referencia_documento,
        receptor=c.receptor_nombre, ubicacion=c.ubicacion_externa, ciudad=c.ciudad) for c in recientes],
        dict(cantidad=payload.cantidad, documento=payload.referencia_documento,
             receptor=payload.receptor_nombre, ubicacion=payload.ubicacion_externa, ciudad=payload.ciudad))
    ultimo_id = db.query(CustodiaExterna.id).filter_by(articulo_id=articulo_id).order_by(
        CustodiaExterna.id.desc()).first()
    confirmar_alertas(db, payload, usuario_id=usuario.id, articulo_id=articulo_id,
                     custodia_id=None, saldo=stock_area, ultimo_id=ultimo_id[0] if ultimo_id else 0,
                     ahora=ahora, alertas=alertas, contexto={"total": apertura.cantidad_actual})
    cambiar_existencia_area(db, apertura, area.id, -payload.cantidad)
    apertura.cantidad_custodia_externa += payload.cantidad
    fila = CustodiaExterna(
        solicitud_id=solicitud_id, solicitud_huella=firma, articulo_id=articulo_id,
        tipo=payload.tipo, area_origen_id=area.id,
        receptor_nombre=payload.receptor_nombre, receptor_tipo=payload.receptor_tipo,
        ubicacion_externa=payload.ubicacion_externa, ciudad=payload.ciudad,
        cantidad_entregada=payload.cantidad, cantidad_fuera=payload.cantidad,
        cantidad_vendida=0, cantidad_devuelta=0,
        total_institucional_entrega=apertura.cantidad_actual,
        encargado_id=payload.encargado_id, registrado_por=usuario.id,
        ocurrido_en=ocurrio, registrado_en=ahora,
        referencia_documento=payload.referencia_documento,
        observaciones=payload.observaciones,
        alertas_control=alertas or None,
        justificacion_alertas=payload.motivo_alertas.strip() if alertas else None,
    )
    db.add(fila)
    try:
        verificar_distribucion(db, apertura)
        registrar_caso(db, fila, "CUSTODIA")
    except IntegrityError:
        db.rollback()
        previa = respuesta_previa()
        if previa is not None:
            return previa
        raise
    auditar(db, usuario, request, "entregar_custodia_externa", "custodia_externa",
            fila.id, {"articulo_id": articulo_id, "tipo": payload.tipo,
                      "solicitud_id": solicitud_id, "area_origen_id": area.id,
                      "cantidad": payload.cantidad, "receptor": payload.receptor_nombre,
                      "ubicacion_externa": payload.ubicacion_externa,
                      "total_institucional": apertura.cantidad_actual,
                      "documento": payload.referencia_documento,
                      "alertas_control": [a["codigo"] for a in alertas],
                      "justificacion_alertas": payload.motivo_alertas.strip() if alertas else None})
    db.commit()
    db.refresh(fila)
    return {"registro": entrega_dict(db, fila),
            "distribucion": distribucion_dict(db, articulo_id, apertura)}


@router.post("/{articulo_id}/custodias-externas/{custodia_id}/eventos")
def registrar_evento(
    articulo_id: int, custodia_id: int, payload: EventoCrear, request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    solicitud_id = str(payload.solicitud_id)
    firma = huella(payload, articulo_id, usuario.id, custodia_id)

    def respuesta_previa():
        previa = db.query(EventoCustodiaExterna).filter_by(solicitud_id=solicitud_id).first()
        if previa is None:
            return None
        if previa.solicitud_huella != firma:
            raise HTTPException(409, "Esta clave ya pertenece a otro evento de custodia.")
        return {"registro": evento_dict(db, previa),
                "custodia": entrega_dict(db, db.get(CustodiaExterna, custodia_id)),
                "distribucion": distribucion_dict(db, articulo_id,
                    db.get(AperturaInventario, articulo_id))}

    previa = respuesta_previa()
    if previa is not None:
        return previa
    if payload.tipo == "VENTA":
        if not (payload.comprador or "").strip():
            raise HTTPException(422, "Identifica al comprador de la venta.")
        if payload.area_destino_id is not None:
            raise HTTPException(422, "Una venta externa no recibe unidades en un área interna.")
    elif payload.area_destino_id is None or payload.comprador:
        raise HTTPException(422, "El retorno requiere un área receptora y no un comprador.")
    encargado_activo(db, payload.encargado_id)

    ahora = datetime.now(UTC)
    apertura = bloquear_apertura(db, articulo_id)
    custodia = db.query(CustodiaExterna).filter_by(
        id=custodia_id, articulo_id=articulo_id).populate_existing().with_for_update().first()
    if custodia is None:
        db.rollback()
        raise HTTPException(404, "Entrega externa no encontrada para este artículo.")
    previa = respuesta_previa()
    if previa is not None:
        db.rollback()
        return previa
    ocurrio = fecha_valida(payload.fecha_operacion, ahora,
                           max(apertura.aprobado_en.replace(tzinfo=UTC)
                               if apertura.aprobado_en.tzinfo is None else apertura.aprobado_en,
                               custodia.ocurrido_en.replace(tzinfo=UTC)
                               if custodia.ocurrido_en.tzinfo is None else custodia.ocurrido_en))
    if payload.cantidad > custodia.cantidad_fuera:
        db.rollback()
        raise HTTPException(409, "La cantidad supera las unidades todavía bajo esta custodia.")

    comparables = db.query(EventoCustodiaExterna).filter_by(
        articulo_id=articulo_id, custodia_id=custodia_id, tipo=payload.tipo,
        area_destino_id=payload.area_destino_id)
    cantidades_previas = [c.cantidad for c in comparables.order_by(EventoCustodiaExterna.id.desc()).limit(20)]
    alertas = evaluar_movimiento(
        tipo="salida" if payload.tipo == "VENTA" else "ingreso",
        cantidad=payload.cantidad, saldo=apertura.cantidad_actual,
        fecha_local=ahora.astimezone(ZoneInfo("America/La_Paz")),
        cantidades_previas=cantidades_previas,
        fecha_operacion_local=ocurrio.astimezone(ZoneInfo("America/La_Paz")) if payload.fecha_operacion else None, **parametros_control(),
    )
    recientes = comparables.filter(EventoCustodiaExterna.registrado_en >= ahora - timedelta(
        minutes=settings.CONTROL_REPETICION_MINUTOS)).all()
    alertas += aviso_repeticion([dict(id=c.id, cantidad=c.cantidad, documento=c.referencia_documento,
                                    comprador=c.comprador) for c in recientes],
        dict(cantidad=payload.cantidad, documento=payload.referencia_documento, comprador=payload.comprador))
    ultimo_id = db.query(EventoCustodiaExterna.id).filter_by(articulo_id=articulo_id).order_by(
        EventoCustodiaExterna.id.desc()).first()
    confirmar_alertas(db, payload, usuario_id=usuario.id, articulo_id=articulo_id,
                     custodia_id=custodia_id, saldo=apertura.cantidad_actual,
                     ultimo_id=ultimo_id[0] if ultimo_id else 0, ahora=ahora,
                     alertas=alertas, contexto={"stock_custodia": custodia.cantidad_fuera})

    custodia.cantidad_fuera -= payload.cantidad
    apertura.cantidad_custodia_externa -= payload.cantidad
    if payload.tipo == "RETORNO":
        cambiar_existencia_area(db, apertura, payload.area_destino_id, payload.cantidad)
        custodia.cantidad_devuelta += payload.cantidad
    else:
        apertura.cantidad_actual -= payload.cantidad
        custodia.cantidad_vendida += payload.cantidad
    fila = EventoCustodiaExterna(
        solicitud_id=solicitud_id, solicitud_huella=firma,
        custodia_id=custodia.id, articulo_id=articulo_id,
        tipo=payload.tipo, cantidad=payload.cantidad,
        area_destino_id=payload.area_destino_id,
        comprador=payload.comprador, encargado_id=payload.encargado_id,
        registrado_por=usuario.id, ocurrido_en=ocurrio, registrado_en=ahora,
        referencia_documento=payload.referencia_documento,
        observaciones=payload.observaciones,
        alertas_control=alertas or None,
        justificacion_alertas=payload.motivo_alertas.strip() if alertas else None,
        total_institucional_despues=apertura.cantidad_actual,
        cantidad_fuera_despues=custodia.cantidad_fuera,
    )
    db.add(fila)
    try:
        verificar_distribucion(db, apertura)
        registrar_caso(db, fila, "EVENTO_CUSTODIA")
    except IntegrityError:
        db.rollback()
        previa = respuesta_previa()
        if previa is not None:
            return previa
        raise
    auditar(db, usuario, request,
            "vender_desde_custodia" if payload.tipo == "VENTA" else "retornar_custodia",
            "evento_custodia_externa", fila.id,
            {"articulo_id": articulo_id, "custodia_id": custodia.id,
             "solicitud_id": solicitud_id, "tipo": payload.tipo,
             "cantidad": payload.cantidad, "cantidad_fuera": custodia.cantidad_fuera,
             "total_institucional": apertura.cantidad_actual,
             "area_destino_id": payload.area_destino_id,
             "comprador": payload.comprador, "documento": payload.referencia_documento,
             "alertas_control": [a["codigo"] for a in alertas],
             "justificacion_alertas": payload.motivo_alertas.strip() if alertas else None})
    db.commit()
    db.refresh(fila)
    return {"registro": evento_dict(db, fila), "custodia": entrega_dict(db, custodia),
            "distribucion": distribucion_dict(db, articulo_id, apertura)}
