from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, DateTime, Integer, Date, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from sqlalchemy import JSON


class LotePendiente(Base):
    __tablename__ = "lotes_pendientes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    extraccion: Mapped[dict] = mapped_column(JSON, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="PENDIENTE", nullable=False)
    lote_id: Mapped[int | None] = mapped_column(ForeignKey("lotes_carga.id"))


class LoteCarga(Base):
    __tablename__ = "lotes_carga"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha_escaneo: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    total_imagenes: Mapped[int] = mapped_column(Integer, nullable=False)


class SolicitudCargaKardex(Base):
    """Una carga por artículo y secuencia exacta de páginas, incluso durante el OCR."""
    __tablename__ = "solicitudes_carga_kardex"
    __table_args__ = (UniqueConstraint("articulo_id", "huella", name="uq_carga_articulo_huella"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), nullable=False)
    huella: Mapped[str] = mapped_column(String(64), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    lote_id: Mapped[int | None] = mapped_column(ForeignKey("lotes_carga.id"))
    pendiente_id: Mapped[str | None] = mapped_column(ForeignKey("lotes_pendientes.id"))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MovimientoKardexArchivado(Base):
    """Copia recuperable de filas de una carga repetida; no alimenta inventario/HIL."""
    __tablename__ = "movimientos_kardex_archivados"

    movimiento_id: Mapped[int] = mapped_column(primary_key=True)
    lote_original_id: Mapped[int] = mapped_column(ForeignKey("lotes_carga.id"), nullable=False)
    lote_canonico_id: Mapped[int] = mapped_column(ForeignKey("lotes_carga.id"), nullable=False)
    datos: Mapped[dict] = mapped_column(JSON, nullable=False)
    archivado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MovimientoKardex(Base):
    __tablename__ = "movimientos_kardex"

    id: Mapped[int] = mapped_column(primary_key=True)
    articulo_id: Mapped[int] = mapped_column(
        ForeignKey("activo.id", ondelete="CASCADE"), nullable=False
    )
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
    fecha_original: Mapped[datetime | None] = mapped_column(Date)
    datos_originales: Mapped[dict | None] = mapped_column(JSON)
    tiene_error_fecha: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    fecha_estado: Mapped[str] = mapped_column(String(30), default="SIN_ALERTA", server_default="SIN_ALERTA", nullable=False)
    saldo_calculado: Mapped[int | None] = mapped_column(Integer)
    observaciones: Mapped[str | None] = mapped_column(Text)
    nodo_grafo: Mapped[str | None] = mapped_column(String(100))
    requiere_auditoria_nodo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    area_estado: Mapped[str] = mapped_column(
        String(40), default="PENDIENTE_HIL", server_default="PENDIENTE_HIL", nullable=False
    )
    referencia_estado: Mapped[str] = mapped_column(
        String(20), default="AUSENTE", server_default="AUSENTE", nullable=False
    )
    requiere_auditoria_referencia: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    # Campos de transacciones modernas (enriquecidas)
    usuario_operador: Mapped[str | None] = mapped_column(String(150))
    tipo_operacion: Mapped[str | None] = mapped_column(String(50))
    receptor: Mapped[str | None] = mapped_column(String(200))
    feria_id: Mapped[int | None] = mapped_column(Integer)
    ciudad_feria: Mapped[str | None] = mapped_column(String(100))
    canal_venta: Mapped[str | None] = mapped_column(String(100))
    motivo_baja: Mapped[str | None] = mapped_column(String(200))
    referencia_documento: Mapped[str | None] = mapped_column(String(200))

    estado: Mapped[str] = mapped_column(
        String(20), default="ACTIVO", server_default="ACTIVO", nullable=False
    )
