"""Cobertura observada y declaraciones humanas sobre documentos faltantes."""

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.activos import Activo
from app.models.cobertura import CoberturaArticulo, TramoCobertura
from app.models.kardex import LoteCarga, MovimientoKardex, SolicitudCargaKardex
from app.models.usuario import Usuario
from app.services.fechas_documentales import fecha_asignable_sql
from app.services.inventario import auditar
from app.services.cierre_documental import fuente_cierre, fila_dict, foto_huella, version_revision
from app.services.fechas_documentales import fecha_asignable


router = APIRouter(prefix="/kardex/cobertura", tags=["Cobertura documental"])


class EstadoCobertura(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    estado: Literal["SIN_CONFIRMAR", "PARCIAL", "CIERRE_CONFIRMADO"]
    referencia: str = Field(min_length=3, max_length=255)
    observacion: str = Field(min_length=10, max_length=2000)
    cierre_movimiento_id: int | None = Field(default=None, gt=0)
    huella_fuente_esperada: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidencia_revisada: bool = False


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


def estado_dict(row: CoberturaArticulo | None, ultimo_lote: int | None, fuente=None) -> dict:
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
            "vigente": (fuente.estado == "CONFIRMADA" if fuente and row.estado == "CIERRE_CONFIRMADO"
                        else row.ultimo_lote_revisado_id == ultimo_lote)}


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
        func.min(case((fecha_asignable_sql(), m.fecha_movimiento))).label("primera_fecha"),
        func.max(case((fecha_asignable_sql(), m.fecha_movimiento))).label("ultima_fecha"),
    ).join(LoteCarga, m.lote_id == LoteCarga.id).filter(
        m.articulo_id == articulo_id, m.estado == "ACTIVO",
    ).group_by(m.lote_id, LoteCarga.tanda, LoteCarga.total_imagenes).order_by(m.lote_id).all()
    anios = db.query(
        case((fecha_asignable_sql(), func.extract("year", m.fecha_movimiento))).label("gestion"), func.count(m.id),
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
    fuente = fuente_cierre(db, articulo_id)
    filas = db.query(m).filter(m.articulo_id == articulo_id, m.lote_id.isnot(None)).all()
    cierre = fuente.cierre if fuente else None
    return {
        "articulo_id": articulo.id, "articulo": articulo.nombre,
        "evidencia_disponible": {
            "lotes": [{"lote_id": g.lote_id, "tanda": g.tanda,
                       "paginas_declaradas": g.total_imagenes,
                       "paginas_con_filas": g.paginas_con_filas,
                       "movimientos": g.filas, "primera_fecha": g.primera_fecha,
                       "ultima_fecha": g.ultima_fecha} for g in grupos],
            "gestiones_con_filas": [{"gestion": int(y) if y is not None else None, "movimientos": n}
                                    for y, n in anios],
            "paginas_con_filas": sum(g.paginas_con_filas for g in grupos),
            "movimientos": sum(g.filas for g in grupos),
        },
        "revision": estado_dict(revision, ultimo_lote, fuente),
        "fuente_cierre": fuente.publico() if fuente else None,
        "huella_fuente": version_revision(fuente, filas),
        "candidatos_cierre": [fila_dict(f) for f in secuencia],
        "continuidad": {
            "orden": "lote, página, fila; la fecha OCR no reordena el papel",
            "interrupciones_entre_lotes": interrupciones,
            "cierre_disponible": fila_dict(cierre),
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
    if db.query(Activo).filter_by(id=articulo_id).with_for_update().first() is None:
        raise HTTPException(404, "Artículo no encontrado")
    ultimo_lote = db.query(func.max(MovimientoKardex.lote_id)).filter(
        MovimientoKardex.articulo_id == articulo_id,
        MovimientoKardex.estado == "ACTIVO").scalar()
    if payload.estado == "CIERRE_CONFIRMADO" and ultimo_lote is None:
        raise HTTPException(409, "No hay cierre documental escaneado que confirmar")
    fuente = fuente_cierre(db, articulo_id)
    row = db.get(CoberturaArticulo, articulo_id)
    anterior = {**estado_dict(row, ultimo_lote, fuente),
                "fuente_cierre": fuente.publico() if fuente else None}
    snapshot = None
    filas = db.query(MovimientoKardex).filter(
        MovimientoKardex.articulo_id == articulo_id, MovimientoKardex.lote_id.isnot(None)).all()
    if (payload.huella_fuente_esperada is not None or payload.estado == "CIERRE_CONFIRMADO"):
        if payload.huella_fuente_esperada != version_revision(fuente, filas):
            raise HTTPException(409, "La evidencia o la revisión cambió. Recarga la cobertura y vuelve a revisar.")
    if payload.estado == "CIERRE_CONFIRMADO":
        if db.query(SolicitudCargaKardex.id).filter(
            SolicitudCargaKardex.articulo_id == articulo_id,
            SolicitudCargaKardex.estado.in_(("PENDIENTE", "PROCESANDO"))).first():
            raise HTTPException(409, "Hay una carga pendiente; termina su revisión antes de confirmar el cierre")
        elegido = next((m for m in filas if m.id == payload.cierre_movimiento_id and m.estado == "ACTIVO"), None)
        if elegido is None or not payload.evidencia_revisada:
            raise HTTPException(409, "Selecciona la fila de cierre y confirma que revisaste su foto")
        foto = foto_huella(elegido.ruta_imagen_respaldo)
        if not foto or not elegido.numero_pagina or not elegido.orden_fila or not fecha_asignable(elegido):
            raise HTTPException(409, "La fila necesita foto accesible, página, orden y fecha documental completa")
        snapshot = {**fila_dict(elegido), "foto_sha256": foto,
                    "referencia": payload.referencia, "motivo": payload.observacion,
                    "revisado_por": usuario.id, "revisado_en": datetime.now(UTC).isoformat()}
    if row is None:
        row = CoberturaArticulo(articulo_id=articulo_id)
        db.add(row)
    row.estado = payload.estado
    row.referencia = payload.referencia
    row.observacion = payload.observacion
    row.ultimo_lote_revisado_id = ultimo_lote
    row.revisado_por = usuario.id
    row.revisado_en = datetime.now(UTC)
    if snapshot:
        row.cierre_movimiento_id = payload.cierre_movimiento_id
        row.cierre_huella_fuente = fuente.huella
        row.cierre_snapshot = snapshot
    auditar(db, usuario, request, "revisar_cobertura_documental", "cobertura_articulo",
            articulo_id, {"anterior": anterior, "nuevo": payload.model_dump(),
                          "ultimo_lote_revisado_id": ultimo_lote, "evidencia_cierre": snapshot})
    db.commit()
    return estado_dict(row, ultimo_lote, fuente_cierre(db, articulo_id))


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
