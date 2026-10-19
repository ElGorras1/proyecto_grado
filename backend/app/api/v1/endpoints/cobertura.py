"""Cobertura observada y declaraciones humanas sobre documentos faltantes."""

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.activos import Activo
from app.models.cobertura import CoberturaArticulo, TramoCobertura
from app.models.kardex import LoteCarga, MovimientoKardex
from app.models.usuario import Usuario
from app.services.inventario import auditar


router = APIRouter(prefix="/kardex/cobertura", tags=["Cobertura documental"])


class EstadoCobertura(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    estado: Literal["SIN_CONFIRMAR", "PARCIAL", "CIERRE_CONFIRMADO"]
    referencia: str = Field(min_length=3, max_length=255)
    observacion: str = Field(min_length=10, max_length=2000)


class TramoNuevo(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    gestion_desde: int = Field(ge=1900, le=2100)
    gestion_hasta: int = Field(ge=1900, le=2100)
    estado: Literal["PENDIENTE", "SIN_CONFIRMAR", "CONFIRMADO"]
    paginas_faltantes: int | None = Field(default=None, ge=0)
    descripcion: str = Field(min_length=10, max_length=2000)
    referencia: str = Field(min_length=3, max_length=255)

    @model_validator(mode="after")
    def validar(self):
        if self.gestion_desde > self.gestion_hasta:
            raise ValueError("La gestión inicial debe preceder a la final")
        if self.estado == "PENDIENTE" and self.paginas_faltantes == 0:
            raise ValueError("Una cobertura pendiente no puede tener cero páginas faltantes")
        return self


def articulo_o_404(db: Session, articulo_id: int) -> Activo:
    articulo = db.get(Activo, articulo_id)
    if articulo is None:
        raise HTTPException(404, "Artículo no encontrado")
    return articulo


def estado_dict(row: CoberturaArticulo | None, ultimo_lote: int | None) -> dict:
    if row is None:
        return {"estado": "SIN_CONFIRMAR", "referencia": None,
                "observacion": "La cobertura todavía no ha sido revisada.",
                "ultimo_lote_revisado_id": None, "revisado_por": None,
                "revisado_en": None, "vigente": False}
    return {"estado": row.estado, "referencia": row.referencia,
            "observacion": row.observacion,
            "ultimo_lote_revisado_id": row.ultimo_lote_revisado_id,
            "revisado_por": row.revisado_por,
            "revisado_en": row.revisado_en.isoformat(),
            "vigente": row.ultimo_lote_revisado_id == ultimo_lote}


@router.get("/{articulo_id}")
def consultar_cobertura(
    articulo_id: int, db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    articulo = articulo_o_404(db, articulo_id)
    m = MovimientoKardex
    grupos = db.query(
        m.lote_id, LoteCarga.tanda, LoteCarga.total_imagenes,
        func.count(m.id).label("filas"),
        func.count(func.distinct(m.numero_pagina)).label("paginas_con_filas"),
        func.min(m.fecha_movimiento).label("primera_fecha"),
        func.max(m.fecha_movimiento).label("ultima_fecha"),
    ).join(LoteCarga, m.lote_id == LoteCarga.id).filter(
        m.articulo_id == articulo_id, m.estado == "ACTIVO",
    ).group_by(m.lote_id, LoteCarga.tanda, LoteCarga.total_imagenes).order_by(m.lote_id).all()
    anios = db.query(
        func.extract("year", m.fecha_movimiento).label("gestion"), func.count(m.id),
    ).filter(m.articulo_id == articulo_id, m.lote_id.isnot(None),
             m.estado == "ACTIVO").group_by("gestion").order_by("gestion").all()
    ultimo_lote = max((g.lote_id for g in grupos), default=None)
    revision = db.get(CoberturaArticulo, articulo_id)
    tramos = db.query(TramoCobertura).filter_by(articulo_id=articulo_id).order_by(
        TramoCobertura.gestion_desde, TramoCobertura.id).all()
    secuencia = db.query(m).filter(
        m.articulo_id == articulo_id, m.lote_id.isnot(None), m.estado == "ACTIVO",
    ).order_by(m.lote_id, func.coalesce(m.orden_pagina_validado, m.numero_pagina), m.orden_fila, m.id).all()
    interrupciones = []
    for anterior, actual in zip(secuencia, secuencia[1:]):
        if anterior.lote_id == actual.lote_id:
            continue
        saldo_esperado = anterior.saldo_registrado + (actual.ingresos or 0) - (actual.salidas or 0)
        if saldo_esperado != actual.saldo_registrado:
            interrupciones.append({"lote_anterior": anterior.lote_id,
                                   "lote_siguiente": actual.lote_id,
                                   "movimiento_anterior": anterior.id,
                                   "movimiento_siguiente": actual.id,
                                   "saldo_esperado": saldo_esperado,
                                   "saldo_documento": actual.saldo_registrado})
    cierre = secuencia[-1] if secuencia else None
    return {
        "articulo_id": articulo.id, "articulo": articulo.nombre,
        "evidencia_disponible": {
            "lotes": [{"lote_id": g.lote_id, "tanda": g.tanda,
                       "paginas_declaradas": g.total_imagenes,
                       "paginas_con_filas": g.paginas_con_filas,
                       "movimientos": g.filas, "primera_fecha": g.primera_fecha,
                       "ultima_fecha": g.ultima_fecha} for g in grupos],
            "gestiones_con_filas": [{"gestion": int(y), "movimientos": n}
                                    for y, n in anios],
            "paginas_con_filas": sum(g.paginas_con_filas for g in grupos),
            "movimientos": sum(g.filas for g in grupos),
        },
        "revision": estado_dict(revision, ultimo_lote),
        "continuidad": {
            "orden": "lote, página, fila; la fecha OCR no reordena el papel",
            "interrupciones_entre_lotes": interrupciones,
            "cierre_disponible": {
                "movimiento_id": cierre.id, "lote_id": cierre.lote_id,
                "pagina": cierre.numero_pagina, "fila": cierre.orden_fila,
                "fecha_ocr": cierre.fecha_movimiento,
                "saldo_documental": cierre.saldo_registrado,
            } if cierre else None,
        },
        "tramos": [{"id": t.id, "gestion_desde": t.gestion_desde,
                    "gestion_hasta": t.gestion_hasta, "estado": t.estado,
                    "paginas_faltantes": t.paginas_faltantes,
                    "descripcion": t.descripcion, "referencia": t.referencia,
                    "revisado_por": t.revisado_por, "revisado_en": t.revisado_en}
                   for t in tramos],
    }


@router.put("/{articulo_id}/revision")
def revisar_cobertura(
    articulo_id: int, payload: EstadoCobertura, request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("Administrador", "Auditor")),
):
    articulo_o_404(db, articulo_id)
    ultimo_lote = db.query(func.max(MovimientoKardex.lote_id)).filter(
        MovimientoKardex.articulo_id == articulo_id,
        MovimientoKardex.estado == "ACTIVO").scalar()
    if payload.estado == "CIERRE_CONFIRMADO" and ultimo_lote is None:
        raise HTTPException(409, "No hay cierre documental escaneado que confirmar")
    row = db.get(CoberturaArticulo, articulo_id)
    anterior = estado_dict(row, ultimo_lote)
    if row is None:
        row = CoberturaArticulo(articulo_id=articulo_id)
        db.add(row)
    row.estado = payload.estado
    row.referencia = payload.referencia
    row.observacion = payload.observacion
    row.ultimo_lote_revisado_id = ultimo_lote
    row.revisado_por = usuario.id
    row.revisado_en = datetime.now(UTC)
    auditar(db, usuario, request, "revisar_cobertura_documental", "cobertura_articulo",
            articulo_id, {"anterior": anterior, "nuevo": payload.model_dump(),
                          "ultimo_lote_revisado_id": ultimo_lote})
    db.commit()
    return estado_dict(row, ultimo_lote)


@router.post("/{articulo_id}/tramos", status_code=201)
def registrar_tramo(
    articulo_id: int, payload: TramoNuevo, request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("Administrador", "Auditor")),
):
    articulo_o_404(db, articulo_id)
    tramo = TramoCobertura(**payload.model_dump(), articulo_id=articulo_id,
                           revisado_por=usuario.id, revisado_en=datetime.now(UTC))
    db.add(tramo)
    db.flush()
    auditar(db, usuario, request, "registrar_tramo_cobertura", "tramo_cobertura",
            tramo.id, {"articulo_id": articulo_id, **payload.model_dump()})
    db.commit()
    return {"id": tramo.id, **payload.model_dump()}
