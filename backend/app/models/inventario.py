"""Saldo operativo independiente de las digitalizaciones históricas."""
from datetime import date, datetime
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class AperturaInventario(Base):
    __tablename__ = "apertura_inventario"
    __table_args__ = (
        CheckConstraint("cantidad_inicial >= 0", name="ck_apertura_inicial"),
        CheckConstraint("cantidad_actual >= 0 AND cantidad_actual <= 2147483647", name="ck_apertura_actual"),
        CheckConstraint("cantidad_sin_ubicacion >= 0", name="ck_apertura_sin_ubicacion"),
        CheckConstraint("cantidad_custodia_externa >= 0 AND cantidad_custodia_externa <= 2147483647", name="ck_apertura_custodia_externa"),
        CheckConstraint("origen IN ('CONTEO_FISICO', 'KARDEX_HISTORICO')", name="ck_apertura_origen"),
    )
    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), primary_key=True)
    cantidad_inicial: Mapped[int] = mapped_column(nullable=False)
    cantidad_actual: Mapped[int] = mapped_column(nullable=False)
    cantidad_sin_ubicacion: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    cantidad_custodia_externa: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    ultimo_moderno_id: Mapped[int] = mapped_column(nullable=False)
    aprobado_por: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    aprobado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    referencia_documento: Mapped[str] = mapped_column(String(255), nullable=False)
    justificacion: Mapped[str] = mapped_column(Text, nullable=False)
    origen: Mapped[str] = mapped_column(String(30), nullable=False, default="CONTEO_FISICO", server_default="CONTEO_FISICO")
    movimiento_historico_id: Mapped[int | None] = mapped_column(Integer)
    lote_historico_id: Mapped[int | None] = mapped_column(Integer)


class ConciliacionInicial(Base):
    """Corte físico único antes de operar: conserva la base y el ajuste explícito."""

    __tablename__ = "conciliacion_inicial"
    __table_args__ = (
        CheckConstraint("cantidad_base >= 0", name="ck_conciliacion_base"),
        CheckConstraint("cantidad_fisica >= 0", name="ck_conciliacion_fisica"),
        CheckConstraint("diferencia = cantidad_fisica - cantidad_base",
                        name="ck_conciliacion_diferencia"),
    )

    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), primary_key=True)
    cantidad_base: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_fisica: Mapped[int] = mapped_column(Integer, nullable=False)
    diferencia: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_conteo: Mapped[date] = mapped_column(Date, nullable=False)
    distribucion_anterior: Mapped[dict] = mapped_column(JSON, nullable=False)
    areas: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    referencia_documento: Mapped[str] = mapped_column(String(255), nullable=False)
    justificacion: Mapped[str] = mapped_column(Text, nullable=False)
    encargado_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    registrado_por: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    origen_base: Mapped[str] = mapped_column(String(30), nullable=False)
    movimiento_historico_id: Mapped[int | None] = mapped_column(Integer)
    ajuste_movimiento_id: Mapped[int | None] = mapped_column(ForeignKey("movimientos_kardex.id"))


class TransferenciaArea(Base):
    """Traslado físico entre ubicaciones sin cambiar el saldo institucional."""

    __tablename__ = "transferencia_area"
    __table_args__ = (
        UniqueConstraint("solicitud_id", name="uq_transferencia_solicitud"),
        CheckConstraint("cantidad > 0", name="ck_transferencia_cantidad"),
        CheckConstraint("area_origen_id <> area_destino_id", name="ck_transferencia_areas"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    solicitud_id: Mapped[str] = mapped_column(String(36), nullable=False)
    solicitud_huella: Mapped[str] = mapped_column(String(64), nullable=False)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), nullable=False)
    area_origen_id: Mapped[int] = mapped_column(ForeignKey("area.id"), nullable=False)
    area_destino_id: Mapped[int] = mapped_column(ForeignKey("area.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    total_institucional: Mapped[int] = mapped_column(Integer, nullable=False)
    encargado_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    registrado_por: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    ocurrido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    referencia_documento: Mapped[str] = mapped_column(String(200), nullable=False)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")
    alertas_control: Mapped[list[dict] | None] = mapped_column(JSON)
    justificacion_alertas: Mapped[str | None] = mapped_column(Text)


class CustodiaExterna(Base):
    """Entrega a feria o consignatario que continúa siendo patrimonio institucional."""

    __tablename__ = "custodia_externa"
    __table_args__ = (
        UniqueConstraint("solicitud_id", name="uq_custodia_solicitud"),
        CheckConstraint("tipo IN ('FERIA', 'CONSIGNACION')", name="ck_custodia_tipo"),
        CheckConstraint("receptor_tipo IN ('PERSONA', 'INSTITUCION')", name="ck_custodia_receptor_tipo"),
        CheckConstraint("cantidad_entregada > 0 AND cantidad_fuera >= 0 AND cantidad_vendida >= 0 AND cantidad_devuelta >= 0", name="ck_custodia_cantidades"),
        CheckConstraint("cantidad_entregada + cantidad_ajustada = cantidad_fuera + cantidad_vendida + cantidad_devuelta AND cantidad_entregada + cantidad_ajustada BETWEEN 0 AND 2147483647", name="ck_custodia_balance"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    solicitud_id: Mapped[str] = mapped_column(String(36), nullable=False)
    solicitud_huella: Mapped[str] = mapped_column(String(64), nullable=False)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    area_origen_id: Mapped[int] = mapped_column(ForeignKey("area.id"), nullable=False)
    receptor_nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    receptor_tipo: Mapped[str] = mapped_column(String(24), nullable=False)
    ubicacion_externa: Mapped[str] = mapped_column(String(200), nullable=False)
    ciudad: Mapped[str | None] = mapped_column(String(100))
    cantidad_entregada: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_ajustada: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    cantidad_fuera: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_vendida: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cantidad_devuelta: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_institucional_entrega: Mapped[int] = mapped_column(Integer, nullable=False)
    encargado_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    registrado_por: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    ocurrido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    referencia_documento: Mapped[str] = mapped_column(String(200), nullable=False)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")
    alertas_control: Mapped[list[dict] | None] = mapped_column(JSON)
    justificacion_alertas: Mapped[str | None] = mapped_column(Text)


class EventoCustodiaExterna(Base):
    """Venta definitiva o retorno parcial de una entrega externa."""

    __tablename__ = "evento_custodia_externa"
    __table_args__ = (
        UniqueConstraint("solicitud_id", name="uq_evento_custodia_solicitud"),
        CheckConstraint("tipo IN ('VENTA', 'RETORNO')", name="ck_evento_custodia_tipo"),
        CheckConstraint("cantidad > 0", name="ck_evento_custodia_cantidad"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    solicitud_id: Mapped[str] = mapped_column(String(36), nullable=False)
    solicitud_huella: Mapped[str] = mapped_column(String(64), nullable=False)
    custodia_id: Mapped[int] = mapped_column(ForeignKey("custodia_externa.id"), nullable=False)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(12), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    area_destino_id: Mapped[int | None] = mapped_column(ForeignKey("area.id"))
    comprador: Mapped[str | None] = mapped_column(String(200))
    encargado_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    registrado_por: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    ocurrido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    referencia_documento: Mapped[str] = mapped_column(String(200), nullable=False)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False, default="")
    alertas_control: Mapped[list[dict] | None] = mapped_column(JSON)
    justificacion_alertas: Mapped[str | None] = mapped_column(Text)
    total_institucional_despues: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_fuera_despues: Mapped[int] = mapped_column(Integer, nullable=False)
