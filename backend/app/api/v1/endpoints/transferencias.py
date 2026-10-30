"""Traslados documentados entre áreas, sin salida del patrimonio institucional."""
import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.activos import Activo
from app.models.area import Area
from app.models.inventario import AperturaInventario, TransferenciaArea
from app.models.usuario import Usuario
from app.core.config import settings
from app.services.control_movimientos import parametros_control, evaluar_movimiento, evaluar_ubicacion, aviso_repeticion, stock_ubicacion, confirmar_alertas
from app.services.control_alertas import registrar_caso
from app.services.rectificaciones_logisticas import estado_vigente, original
from app.services.inventario import (
    auditar, bloquear_apertura, cambiar_existencia_area, distribucion_dict,
    verificar_distribucion,
)


router = APIRouter(prefix="/kardex/articulos", tags=["Transferencias entre áreas"])


class TransferenciaCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    solicitud_id: uuid.UUID
    area_origen_id: int = Field(gt=0)
    area_destino_id: int = Field(gt=0)
    cantidad: int = Field(strict=True, gt=0, le=2147483647)
    encargado_id: int = Field(gt=0)
    fecha_operacion: AwareDatetime | None = None
    referencia_documento: str = Field(min_length=3, max_length=200)
    observaciones: str = Field(default="", max_length=1000)
    confirmacion_alertas: str | None = Field(default=None, min_length=64, max_length=64)
    motivo_alertas: str = Field(default="", max_length=1000)


def registro_dict(db: Session, fila: TransferenciaArea) -> dict:
    vigente, version, rect = estado_vigente(db, "TRANSFERENCIA", fila)
    origen = db.get(Area, vigente["area_origen_id"])
    destino = db.get(Area, vigente["area_destino_id"])
    return {campo: getattr(fila, campo) for campo in (
        "id", "solicitud_id", "articulo_id", "area_origen_id", "area_destino_id",
        "cantidad", "total_institucional", "encargado_id", "registrado_por",
        "ocurrido_en", "registrado_en", "referencia_documento", "observaciones",
        "alertas_control", "justificacion_alertas",
    )} | vigente | {"area_origen": origen.nombre if origen else None,
         "area_destino": destino.nombre if destino else None, "datos_originales": original("TRANSFERENCIA", fila),
         "datos_vigentes": vigente, "version_rectificacion": version, "ultima_rectificacion_id": rect.id if rect else None}


@router.get("/{articulo_id}/transferencias")
def listar_transferencias(
    articulo_id: int, db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    if db.get(Activo, articulo_id) is None:
        raise HTTPException(404, "Artículo no encontrado")
    filas = db.query(TransferenciaArea).filter_by(articulo_id=articulo_id).order_by(
        TransferenciaArea.id.desc()).all()
    return [registro_dict(db, fila) for fila in filas]


@router.post("/{articulo_id}/transferencias")
def registrar_transferencia(
    articulo_id: int, payload: TransferenciaCrear, request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    solicitud_id = str(payload.solicitud_id)
    contenido = payload.model_dump(mode="json", exclude={"confirmacion_alertas", "motivo_alertas"}) | {
        "articulo_id": articulo_id, "registrado_por": usuario.id}
    huella = hashlib.sha256(json.dumps(
        contenido, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode()).hexdigest()

    def respuesta_previa():
        fila = db.query(TransferenciaArea).filter_by(solicitud_id=solicitud_id).first()
        if fila is None:
            return None
        if fila.solicitud_huella != huella:
            raise HTTPException(409, "Esta clave ya pertenece a otra transferencia. Inicia una solicitud nueva.")
        return {"registro": registro_dict(db, fila),
                "distribucion": distribucion_dict(
                    db, articulo_id, db.get(AperturaInventario, articulo_id))}

    previa = respuesta_previa()
    if previa is not None:
        return previa
    if payload.area_origen_id == payload.area_destino_id:
        raise HTTPException(422, "El origen y el destino deben ser áreas distintas.")
    origen = db.get(Area, payload.area_origen_id)
    destino = db.get(Area, payload.area_destino_id)
    if origen is None or destino is None or origen.estado != "activo" or destino.estado != "activo":
        raise HTTPException(422, "Selecciona dos áreas operativas activas.")
    encargado = db.get(Usuario, payload.encargado_id)
    if encargado is None or encargado.estado != "activo":
        raise HTTPException(422, "Selecciona un encargado activo.")

    ahora = datetime.now(UTC)
    ocurrio = payload.fecha_operacion.astimezone(UTC) if payload.fecha_operacion else ahora
    if ocurrio > ahora + timedelta(minutes=5):
        raise HTTPException(422, "La fecha de la transferencia no puede estar en el futuro.")
    # Bloquea la distribución completa del artículo; las entradas/salidas usan el mismo corte.
    apertura = bloquear_apertura(db, articulo_id)
    previa = respuesta_previa()
    if previa is not None:
        db.rollback()
        return previa
    inicio = apertura.aprobado_en
    if inicio.tzinfo is None:  # SQLite en pruebas.
        inicio = inicio.replace(tzinfo=UTC)
    if ocurrio < inicio:
        db.rollback()
        raise HTTPException(409, "La transferencia ocurrió antes del corte de apertura; concilia ese periodo primero.")

    total = apertura.cantidad_actual
    stock_origen = stock_ubicacion(db, apertura, origen.id)
    if payload.cantidad > stock_origen:
        db.rollback()
        raise HTTPException(409, "Stock insuficiente en el área de origen.")
    comparables = db.query(TransferenciaArea).filter_by(
        articulo_id=articulo_id, area_origen_id=origen.id, area_destino_id=destino.id)
    cantidades = [estado_vigente(db, "TRANSFERENCIA", f)[0]["cantidad"] for f in comparables.order_by(TransferenciaArea.id.desc()).limit(20)]
    alertas = evaluar_movimiento(tipo="ingreso", cantidad=payload.cantidad, saldo=total,
        fecha_local=ahora.astimezone(ZoneInfo("America/La_Paz")),
        fecha_operacion_local=ocurrio.astimezone(ZoneInfo("America/La_Paz")) if payload.fecha_operacion else None,
        cantidades_previas=cantidades, **parametros_control())
    alertas += evaluar_ubicacion(cantidad=payload.cantidad, saldo=stock_origen,
        codigo_total="AGOTA_AREA_POR_TRANSFERENCIA", codigo_mayoria="TRANSFERENCIA_MAYORITARIA_AREA",
        etiqueta="el área de origen al transferir", porcentaje=settings.CONTROL_PORCENTAJE_MAYORITARIO,
        minimo=settings.CONTROL_STOCK_MINIMO_MAYORITARIO)
    recientes = comparables.filter(TransferenciaArea.registrado_en >= ahora - timedelta(
        minutes=settings.CONTROL_REPETICION_MINUTOS)).all()
    alertas += aviso_repeticion([dict(id=f.id, cantidad=f.cantidad, documento=f.referencia_documento) for f in recientes],
        dict(cantidad=payload.cantidad, documento=payload.referencia_documento))
    ultimo = db.query(TransferenciaArea.id).filter_by(articulo_id=articulo_id).order_by(TransferenciaArea.id.desc()).first()
    confirmar_alertas(db, payload, usuario_id=usuario.id, articulo_id=articulo_id,
        custodia_id=None, saldo=stock_origen, ultimo_id=ultimo[0] if ultimo else 0,
        ahora=ahora, alertas=alertas, contexto={"clase": "TRANSFERENCIA", "total": total,
            "stock_destino": stock_ubicacion(db, apertura, destino.id)})
    cambiar_existencia_area(db, apertura, origen.id, -payload.cantidad)
    cambiar_existencia_area(db, apertura, destino.id, payload.cantidad)
    fila = TransferenciaArea(
        solicitud_id=solicitud_id, solicitud_huella=huella,
        articulo_id=articulo_id, area_origen_id=origen.id,
        area_destino_id=destino.id, cantidad=payload.cantidad,
        total_institucional=total, encargado_id=encargado.id,
        registrado_por=usuario.id, ocurrido_en=ocurrio, registrado_en=ahora,
        referencia_documento=payload.referencia_documento,
        observaciones=payload.observaciones,
        alertas_control=alertas or None, justificacion_alertas=payload.motivo_alertas if alertas else None,
    )
    db.add(fila)
    try:
        verificar_distribucion(db, apertura)
        registrar_caso(db, fila, "TRANSFERENCIA")
    except IntegrityError:
        db.rollback()
        previa = respuesta_previa()
        if previa is not None:
            return previa
        raise
    auditar(db, usuario, request, "transferir_existencia_area", "transferencia_area",
            fila.id, {"articulo_id": articulo_id, "solicitud_id": solicitud_id,
                      "area_origen_id": origen.id, "area_destino_id": destino.id,
                      "cantidad": payload.cantidad, "total_institucional": total,
                      "encargado_id": encargado.id, "registrado_por": usuario.id,
                      "ocurrido_en": ocurrio.isoformat(), "registrado_en": ahora.isoformat(),
                      "referencia_documento": payload.referencia_documento,
                      "alertas_control": [a["codigo"] for a in alertas],
                      "justificacion_alertas": payload.motivo_alertas if alertas else None})
    db.commit()
    db.refresh(fila)
    return {"registro": registro_dict(db, fila),
            "distribucion": distribucion_dict(db, articulo_id, apertura)}
