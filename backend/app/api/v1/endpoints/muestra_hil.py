"""Muestras congeladas de Kárdex migrado y decisiones documentales humanas."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import case
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.crud.auditoria import registrar_evento_auditoria
from app.db.session import get_db
from app.models.activos import Activo
from app.models.auditoria import AuditoriaSistema
from app.models.kardex import LoteCarga, MovimientoKardex
from app.models.usuario import Usuario
from app.schemas.kardex import MovimientoKardexOut
from app.services.calidad_kardex import pendiente_hil_sql, tipos_alerta
from app.services.muestra_hil import huella_fila, seleccionar_ids


router = APIRouter(prefix="/kardex/muestras-validacion", tags=["Validación humana"])


class CrearMuestra(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    tanda: int | None = Field(default=None, ge=1, le=9999)
    tamano: int = Field(default=30, ge=1, le=100)
    semilla: str = Field(default="revision-institucional", min_length=1, max_length=80)


class RevisarFila(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    resultado: Literal["COINCIDE_DOCUMENTO", "DIFERENCIA_DOCUMENTO"]
    motivo: str = Field(min_length=10, max_length=1000)
    huella_fila: str = Field(min_length=64, max_length=64)


def obtener_muestra(db: Session, muestra_id: int) -> AuditoriaSistema:
    muestra = db.get(AuditoriaSistema, muestra_id)
    if not muestra or muestra.accion != "crear_muestra_hil" or muestra.recurso != "muestra_hil":
        raise HTTPException(404, "Muestra no encontrada")
    return muestra


@router.get("")
def listar_muestras(
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    muestras = db.query(AuditoriaSistema, Usuario.nombre).outerjoin(
        Usuario, Usuario.id == AuditoriaSistema.usuario_id,
    ).filter(AuditoriaSistema.accion == "crear_muestra_hil").order_by(
        AuditoriaSistema.id.desc(),
    ).limit(30).all()
    return [{"id": evento.id, "creada_en": evento.fecha_hora,
             "creada_por": nombre or "Usuario no disponible", **evento.detalle}
            for evento, nombre in muestras]


@router.post("")
def crear_muestra(
    payload: CrearMuestra,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("Administrador", "Auditor")),
):
    alerta = case((pendiente_hil_sql(), 1), else_=0)
    consulta = db.query(MovimientoKardex.id, LoteCarga.tanda, alerta).join(
        LoteCarga, LoteCarga.id == MovimientoKardex.lote_id,
    ).filter(MovimientoKardex.estado == "ACTIVO",
             MovimientoKardex.ruta_imagen_respaldo.isnot(None))
    if payload.tanda is not None:
        consulta = consulta.filter(LoteCarga.tanda == payload.tanda)
    estratos: dict[str, list[int]] = {}
    for movimiento_id, tanda, pendiente in consulta.all():
        clave = f"tanda_{tanda}_{'pendiente' if pendiente else 'sin_alerta'}"
        estratos.setdefault(clave, []).append(movimiento_id)
    if not estratos:
        raise HTTPException(409, "No hay filas históricas con fotografía para esta muestra")
    ids = seleccionar_ids(estratos, payload.tamano, payload.semilla)
    detalle = {"tanda": payload.tanda, "tamano_solicitado": payload.tamano,
               "semilla": payload.semilla, "metodo": "huella_id_por_estrato_v1",
               "elegibles": sum(map(len, estratos.values())),
               "estratos": {nombre: len(filas) for nombre, filas in estratos.items()},
               "ids": ids, "corte_id": max(max(filas) for filas in estratos.values())}
    evento = registrar_evento_auditoria(
        db, usuario_id=usuario.id, accion="crear_muestra_hil", recurso="muestra_hil",
        recurso_id=None, resultado="exito",
        ip_origen=request.client.host if request.client else None, detalle=detalle,
    )
    return {"id": evento.id, "creada_en": evento.fecha_hora, **detalle}


@router.get("/{muestra_id}")
def ver_muestra(
    muestra_id: int,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    muestra = obtener_muestra(db, muestra_id)
    ids = muestra.detalle["ids"]
    filas = db.query(MovimientoKardex, Activo.nombre).options(
        selectinload(MovimientoKardex.lote),
    ).join(Activo, Activo.id == MovimientoKardex.articulo_id).filter(
        MovimientoKardex.id.in_(ids),
    ).all()
    por_id = {mov.id: (mov, nombre) for mov, nombre in filas}
    revisiones = db.query(AuditoriaSistema, Usuario.nombre).outerjoin(
        Usuario, Usuario.id == AuditoriaSistema.usuario_id,
    ).filter(AuditoriaSistema.accion == "validar_muestra_hil",
             AuditoriaSistema.recurso_id.in_(ids)).order_by(
        AuditoriaSistema.id.desc(),
    ).all()
    ultimas = {}
    for evento, nombre in revisiones:
        if evento.detalle.get("muestra_id") == muestra_id:
            ultimas.setdefault(evento.recurso_id, (evento, nombre))
    resultado = []
    for movimiento_id in ids:
        if movimiento_id not in por_id:
            resultado.append({"id": movimiento_id, "no_disponible": True})
            continue
        mov, nombre_articulo = por_id[movimiento_id]
        revision, revisor = ultimas.get(movimiento_id, (None, None))
        dto = MovimientoKardexOut.model_validate(mov).model_dump(mode="json")
        dto["articulo_nombre"] = nombre_articulo
        dto["tipos_alerta"] = tipos_alerta(mov)
        dto["huella_actual"] = huella_fila(mov)
        dto["revision"] = ({"resultado": revision.detalle["resultado"],
                            "motivo": revision.detalle["motivo"],
                            "revisor": revisor or "Usuario no disponible",
                            "fecha": revision.fecha_hora,
                            "vigente": revision.detalle["huella_fila"] == dto["huella_actual"]}
                           if revision else None)
        resultado.append(dto)
    resumen = {
        "sin_revisar": sum(fila.get("revision") is None for fila in resultado),
        "coinciden": sum(fila.get("revision") is not None and
                         fila["revision"]["vigente"] and
                         fila["revision"]["resultado"] == "COINCIDE_DOCUMENTO"
                         for fila in resultado),
        "diferencias": sum(fila.get("revision") is not None and
                           fila["revision"]["vigente"] and
                           fila["revision"]["resultado"] == "DIFERENCIA_DOCUMENTO"
                           for fila in resultado),
        "desactualizadas": sum(fila.get("revision") is not None and
                                not fila["revision"]["vigente"] for fila in resultado),
    }
    return {"id": muestra.id, "creada_en": muestra.fecha_hora,
            **muestra.detalle, "resumen": resumen, "filas": resultado}


@router.post("/{muestra_id}/movimientos/{movimiento_id}/revision")
def revisar_fila(
    muestra_id: int,
    movimiento_id: int,
    payload: RevisarFila,
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("Administrador", "Auditor")),
):
    muestra = obtener_muestra(db, muestra_id)
    if movimiento_id not in muestra.detalle["ids"]:
        raise HTTPException(404, "La fila no pertenece a esta muestra")
    movimiento = db.query(MovimientoKardex).filter(
        MovimientoKardex.id == movimiento_id,
        MovimientoKardex.lote_id.isnot(None),
        MovimientoKardex.estado == "ACTIVO",
    ).first()
    if not movimiento or not movimiento.ruta_imagen_respaldo:
        raise HTTPException(409, "La fila ya no tiene evidencia documental disponible")
    huella_actual = huella_fila(movimiento)
    if payload.huella_fila != huella_actual:
        raise HTTPException(409, "La fila cambió desde que abriste la muestra. Vuelve a cargarla antes de decidir.")
    evento = registrar_evento_auditoria(
        db, usuario_id=usuario.id, accion="validar_muestra_hil",
        recurso="movimientos_kardex", recurso_id=movimiento_id,
        resultado="exito", ip_origen=request.client.host if request.client else None,
        detalle={"muestra_id": muestra_id, "resultado": payload.resultado,
                 "motivo": payload.motivo.strip(), "huella_fila": huella_actual,
                 "ruta_imagen": movimiento.ruta_imagen_respaldo},
    )
    return {"id": evento.id, "resultado": payload.resultado,
            "fecha": evento.fecha_hora, "movimiento_id": movimiento_id}
