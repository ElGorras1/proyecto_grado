import hashlib
import json
from datetime import UTC, datetime
from typing import Annotated, Literal, Union
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.area import Area
from app.models.activos import Activo
from app.models.inventario import CustodiaExterna
from app.models.rectificacion_logistica import RectificacionLogistica as R
from app.models.usuario import Usuario
from app.services.inventario import auditar, bloquear_apertura, cambiar_existencia_area, distribucion_dict, verificar_distribucion
from app.services.control_movimientos import stock_ubicacion
from app.services.rectificaciones_logisticas import MODELOS, estado_vigente, diferencia, registro_dict

router = APIRouter(prefix="/kardex/articulos", tags=["Rectificaciones logísticas"])


class DatosComunes(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    cantidad: int = Field(strict=True, ge=0, le=2147483647)
    encargado_id: int = Field(gt=0)
    referencia_documento: str = Field(min_length=3, max_length=200)
    observaciones: str = Field(default="", max_length=1000)


class TransferenciaCorregida(DatosComunes):
    clase: Literal["TRANSFERENCIA"]
    area_origen_id: int = Field(gt=0)
    area_destino_id: int = Field(gt=0)

    @model_validator(mode="after")
    def validar(self):
        if self.area_origen_id == self.area_destino_id:
            raise ValueError("El origen y el destino deben ser distintos")
        return self


class EntregaCorregida(DatosComunes):
    clase: Literal["ENTREGA"]
    tipo: Literal["FERIA", "CONSIGNACION"]
    area_origen_id: int = Field(gt=0)
    receptor_nombre: str = Field(min_length=3, max_length=200)
    receptor_tipo: Literal["PERSONA", "INSTITUCION"]
    ubicacion_externa: str = Field(min_length=3, max_length=200)
    ciudad: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validar(self):
        if self.tipo == "FERIA" and not (self.ciudad or "").strip():
            raise ValueError("La feria requiere ciudad")
        return self


class EventoCorregido(DatosComunes):
    clase: Literal["EVENTO_CUSTODIA"]
    tipo: Literal["VENTA", "RETORNO"]
    area_destino_id: int | None = Field(default=None, gt=0)
    comprador: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validar(self):
        if self.tipo == "VENTA" and (not (self.comprador or "").strip() or self.area_destino_id is not None):
            raise ValueError("La venta requiere comprador y no recibe en un área")
        if self.tipo == "RETORNO" and (self.area_destino_id is None or self.comprador):
            raise ValueError("El retorno requiere área receptora y no comprador")
        return self


class RectificacionCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    solicitud_id: UUID
    registro_id: int = Field(gt=0)
    version_esperada: str = Field(pattern="^[a-f0-9]{64}$")
    cambios: Annotated[Union[TransferenciaCorregida, EntregaCorregida, EventoCorregido], Field(discriminator="clase")]
    referencia_documento: str = Field(min_length=3, max_length=200)
    motivo: str = Field(min_length=10, max_length=2000)
    evidencia_revisada: bool


@router.get("/{articulo_id}/rectificaciones-logisticas")
def listar(articulo_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if not db.get(Activo, articulo_id):
        raise HTTPException(404, "Artículo no encontrado")
    return [registro_dict(db, r) for r in db.query(R).filter_by(articulo_id=articulo_id).order_by(R.id)]


@router.post("/{articulo_id}/rectificaciones-logisticas")
def rectificar(articulo_id: int, payload: RectificacionCrear, request: Request,
               db: Session = Depends(get_db), usuario=Depends(require_roles("Administrador"))):
    firma = hashlib.sha256(json.dumps(
        {**payload.model_dump(mode="json"), "articulo_id": articulo_id, "usuario_id": usuario.id},
        sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    def previa():
        fila = db.query(R).filter_by(solicitud_id=str(payload.solicitud_id)).first()
        if fila:
            if fila.solicitud_huella != firma:
                raise HTTPException(409, "La solicitud ya pertenece a otra corrección; conserva la clave solo para reintentar el mismo envío.")
            return {"registro": registro_dict(db, fila)}
    respuesta = previa()
    if respuesta:
        return respuesta
    apertura = bloquear_apertura(db, articulo_id)
    respuesta = previa()
    if respuesta:
        return respuesta
    clase = payload.cambios.clase
    modelo = MODELOS[clase]
    original = db.query(modelo).filter_by(id=payload.registro_id, articulo_id=articulo_id).populate_existing().with_for_update().first()
    if original is None:
        raise HTTPException(404, "El registro no corresponde a este artículo")
    custodia = None
    if clase != "TRANSFERENCIA":
        cid = original.id if clase == "ENTREGA" else original.custodia_id
        custodia = db.query(CustodiaExterna).filter_by(id=cid, articulo_id=articulo_id).populate_existing().with_for_update().one()
    antes, version, anterior = estado_vigente(db, clase, original)
    if payload.version_esperada != version:
        raise HTTPException(409, "El registro o su custodia cambió; recarga y revisa sus valores.")
    if not payload.evidencia_revisada:
        raise HTTPException(422, "Confirma que cotejaste la corrección con su evidencia")
    nuevo = payload.cambios.model_dump(exclude={"clase"})
    if nuevo == antes:
        raise HTTPException(409, "No hay cambios respecto de los datos vigentes")
    encargado = db.get(Usuario, nuevo["encargado_id"])
    if not encargado or encargado.estado != "activo":
        raise HTTPException(422, "Selecciona un encargado activo")
    delta = diferencia(clase, antes, nuevo)
    total = apertura.cantidad_actual + delta["total"]
    fuera = apertura.cantidad_custodia_externa + delta["fuera"]
    if not 0 <= total <= 2147483647 or not 0 <= fuera <= 2147483647:
        raise HTTPException(409, "La compensación dejaría un saldo institucional o externo inválido")
    if custodia:
        valores = [custodia.cantidad_fuera + delta["fuera"], custodia.cantidad_vendida + delta["vendida"],
                   custodia.cantidad_devuelta + delta["devuelta"]]
        if any(not 0 <= v <= 2147483647 for v in valores):
            raise HTTPException(409, "La corrección supera lo disponible o contradice ventas/retornos posteriores")
        if clase == "ENTREGA" and nuevo["cantidad"] < custodia.cantidad_vendida + custodia.cantidad_devuelta:
            raise HTTPException(409, "La entrega corregida no puede ser menor que las ventas y retornos vigentes")
    ids = set(delta["areas"])
    # Una ubicación nueva del documento también debe estar vigente, aunque el neto sea cero.
    ids.update(v for k, v in nuevo.items() if k in ("area_origen_id", "area_destino_id") and v)
    areas = {a.id: a for a in db.query(Area).filter(Area.id.in_(ids)).order_by(Area.id).populate_existing().with_for_update(read=True)}
    if any(id not in areas or areas[id].estado != "activo" for id in ids):
        raise HTTPException(409, "La compensación requiere ubicaciones operativas activas; revisa o reactiva las áreas con autorización.")
    for id, cambio in delta["areas"].items():
        if stock_ubicacion(db, apertura, id) + cambio < 0:
            raise HTTPException(409, "La compensación no tiene unidades disponibles en una de las áreas; revisa los hechos posteriores.")
    try:
        for id, cambio in sorted(delta["areas"].items()):
            cambiar_existencia_area(db, apertura, id, cambio)
        apertura.cantidad_actual = total
        apertura.cantidad_custodia_externa = fuera
        if custodia:
            custodia.cantidad_fuera += delta["fuera"]
            custodia.cantidad_vendida += delta["vendida"]
            custodia.cantidad_devuelta += delta["devuelta"]
            if clase == "ENTREGA":
                custodia.cantidad_ajustada += nuevo["cantidad"] - antes["cantidad"]
        fila = R(solicitud_id=str(payload.solicitud_id), solicitud_huella=firma, articulo_id=articulo_id,
            clase=clase, transferencia_id=original.id if clase == "TRANSFERENCIA" else None,
            custodia_id=custodia.id if custodia else None, evento_custodia_id=original.id if clase == "EVENTO_CUSTODIA" else None,
            anterior_id=anterior.id if anterior else None, previo=antes, nuevo=nuevo,
            areas_delta=[{"area_id": id, "delta": d} for id, d in sorted(delta["areas"].items())],
            delta_total=delta["total"], delta_custodia=delta["fuera"], total_despues=total,
            custodia_despues=custodia.cantidad_fuera if custodia else 0,
            registrado_por=usuario.id, registrado_en=datetime.now(UTC),
            referencia_documento=payload.referencia_documento, motivo=payload.motivo)
        db.add(fila)
        verificar_distribucion(db, apertura)
        auditar(db, usuario, request, "rectificar_logistica", "rectificacion_logistica", fila.id,
                {"clase": clase, "original_id": original.id, "previo": antes, "nuevo": nuevo,
                 "delta_total": delta["total"], "delta_custodia": delta["fuera"], "areas_delta": fila.areas_delta,
                 "motivo": payload.motivo, "referencia_documento": payload.referencia_documento,
                 "autorizado_por_id": usuario.id})
        db.commit()
    except IntegrityError:
        db.rollback()
        respuesta = previa()
        if respuesta:
            return respuesta
        raise
    return {"registro": registro_dict(db, fila), "distribucion": distribucion_dict(db, articulo_id, apertura)}
