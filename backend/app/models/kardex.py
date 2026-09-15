from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, DateTime, Integer, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

class LoteCarga(Base):
    __tablename__ = "lotes_carga"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha_escaneo: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    total_imagenes: Mapped[int] = mapped_column(Integer, nullable=False)


class MovimientoKardex(Base):
    __tablename__ = "movimientos_kardex"

    id: Mapped[int] = mapped_column(primary_key=True)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id", ondelete="CASCADE"), nullable=False)
    lote_id: Mapped[int | None] = mapped_column(ForeignKey("lotes_carga.id", ondelete="SET NULL"))
    
    fecha_movimiento: Mapped[datetime] = mapped_column(Date, nullable=False)
    detalle: Mapped[str] = mapped_column(Text, nullable=False)
    referencia: Mapped[str | None] = mapped_column(String(100))
    area: Mapped[str | None] = mapped_column(String(100))
    
    ingresos: Mapped[int | None] = mapped_column(Integer, default=None)
    salidas: Mapped[int | None] = mapped_column(Integer, default=None)
    saldo_registrado: Mapped[int] = mapped_column(Integer, nullable=False)
    
    ruta_imagen_respaldo: Mapped[str | None] = mapped_column(String(512))
    numero_pagina: Mapped[int | None] = mapped_column(Integer)
    orden_fila: Mapped[int | None] = mapped_column(Integer)

    # Campos de auditoría (Requerimiento 1)
    tiene_error_saldo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    saldo_calculado: Mapped[int | None] = mapped_column(Integer)
    observaciones: Mapped[str | None] = mapped_column(Text)
    nodo_grafo: Mapped[str | None] = mapped_column(String(100))
    requiere_auditoria_nodo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
