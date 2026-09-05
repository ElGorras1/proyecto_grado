from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, Numeric, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TipoMovimiento(Base):
    __tablename__ = "tipo_movimiento"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    afecta_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    estado: Mapped[str] = mapped_column(String(20), default="activo")


class Movimiento(Base):
    """
    Registro central del Kardex digital: entradas, salidas y
    transferencias. 'encargado_id' (persona responsable del movimiento) y
    'usuario_registrador_id' (cuenta que ejecuta el registro) son
    conceptos separados a propósito, tal como exige el documento de
    requisitos, aunque puedan coincidir.
    """

    __tablename__ = "movimiento"

    id: Mapped[int] = mapped_column(primary_key=True)
    activo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), nullable=False)
    tipo_movimiento_id: Mapped[int] = mapped_column(ForeignKey("tipo_movimiento.id"), nullable=False)
    area_origen_id: Mapped[int | None] = mapped_column(ForeignKey("area.id"))
    area_destino_id: Mapped[int | None] = mapped_column(ForeignKey("area.id"))
    encargado_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    usuario_registrador_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    movimiento_origen_id: Mapped[int | None] = mapped_column(ForeignKey("movimiento.id"))
    documento_legacy_id: Mapped[int | None] = mapped_column(ForeignKey("documento_legacy.id"))
    ubicacion_evento_id: Mapped[int | None] = mapped_column(ForeignKey("ubicacion_evento.id"))
    cantidad: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    saldo_resultante: Mapped[float | None] = mapped_column(Numeric(14, 2))
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    motivo: Mapped[str | None] = mapped_column(String(255))
    observacion: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="activo")
