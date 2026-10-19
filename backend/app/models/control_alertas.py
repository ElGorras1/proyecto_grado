"""Seguimiento de avisos operativos, separado del stock y del histórico OCR."""
from datetime import UTC, datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

ESTADOS = ("PENDIENTE", "EN_REVISION", "SEGUIMIENTO", "JUSTIFICADO", "CERRADO")
PRIORIDADES = ("ALTA", "MEDIA", "BAJA")

class CasoControl(Base):
    __tablename__ = "caso_control"
    __table_args__ = (
        CheckConstraint("estado IN ('PENDIENTE','EN_REVISION','SEGUIMIENTO','JUSTIFICADO','CERRADO')", name="ck_caso_control_estado"),
        CheckConstraint("prioridad IN ('ALTA','MEDIA','BAJA')", name="ck_caso_control_prioridad"),
        CheckConstraint("(CASE WHEN movimiento_id IS NULL THEN 0 ELSE 1 END + CASE WHEN transferencia_id IS NULL THEN 0 ELSE 1 END + CASE WHEN custodia_id IS NULL THEN 0 ELSE 1 END + CASE WHEN evento_custodia_id IS NULL THEN 0 ELSE 1 END) = 1", name="ck_caso_control_origen"),
        UniqueConstraint("movimiento_id", name="uq_caso_control_movimiento"),
        UniqueConstraint("transferencia_id", name="uq_caso_control_transferencia"),
        UniqueConstraint("custodia_id", name="uq_caso_control_custodia"),
        UniqueConstraint("evento_custodia_id", name="uq_caso_control_evento"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), index=True)
    movimiento_id: Mapped[int | None] = mapped_column(ForeignKey("movimientos_kardex.id"))
    transferencia_id: Mapped[int | None] = mapped_column(ForeignKey("transferencia_area.id"))
    custodia_id: Mapped[int | None] = mapped_column(ForeignKey("custodia_externa.id"))
    evento_custodia_id: Mapped[int | None] = mapped_column(ForeignKey("evento_custodia_externa.id"))
    estado: Mapped[str] = mapped_column(String(24), default="PENDIENTE", nullable=False, index=True)
    prioridad: Mapped[str] = mapped_column(String(10), nullable=False)
    asignado_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    asignado_nombre: Mapped[str | None] = mapped_column(String(120))
    revision_numero: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actualizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    conclusion: Mapped[str | None] = mapped_column(String(30))
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    codigos: Mapped[list[str]] = mapped_column(JSON, nullable=False)

class RevisionControl(Base):
    __tablename__ = "revision_control"
    __table_args__ = (UniqueConstraint("solicitud_id", name="uq_revision_control_solicitud"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    caso_id: Mapped[int] = mapped_column(ForeignKey("caso_control.id"), index=True)
    solicitud_id: Mapped[str] = mapped_column(String(36), nullable=False)
    solicitud_huella: Mapped[str] = mapped_column(String(64), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    usuario_nombre: Mapped[str] = mapped_column(String(120))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    anterior: Mapped[dict] = mapped_column(JSON, nullable=False)
    nuevo: Mapped[dict] = mapped_column(JSON, nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    documento: Mapped[str | None] = mapped_column(String(200))
    correccion_movimiento_id: Mapped[int | None] = mapped_column(ForeignKey("movimientos_kardex.id"))
    huella_contexto: Mapped[str] = mapped_column(String(64), nullable=False)
