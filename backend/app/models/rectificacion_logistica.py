"""Compensaciones logísticas: originales intactos y decisiones encadenadas."""
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class RectificacionLogistica(Base):
    __tablename__ = "rectificacion_logistica"
    __table_args__ = (
        CheckConstraint(
            "(clase='TRANSFERENCIA' AND transferencia_id IS NOT NULL AND custodia_id IS NULL AND evento_custodia_id IS NULL) OR "
            "(clase='ENTREGA' AND transferencia_id IS NULL AND custodia_id IS NOT NULL AND evento_custodia_id IS NULL) OR "
            "(clase='EVENTO_CUSTODIA' AND transferencia_id IS NULL AND custodia_id IS NOT NULL AND evento_custodia_id IS NOT NULL)",
            name="ck_rectificacion_logistica_origen"),
        CheckConstraint("anterior_id IS NULL OR anterior_id<>id", name="ck_rectificacion_logistica_no_reflexiva"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    solicitud_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    solicitud_huella: Mapped[str] = mapped_column(String(64), nullable=False)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), nullable=False, index=True)
    clase: Mapped[str] = mapped_column(String(24), nullable=False)
    transferencia_id: Mapped[int | None] = mapped_column(ForeignKey("transferencia_area.id"))
    custodia_id: Mapped[int | None] = mapped_column(ForeignKey("custodia_externa.id"))
    evento_custodia_id: Mapped[int | None] = mapped_column(ForeignKey("evento_custodia_externa.id"))
    anterior_id: Mapped[int | None] = mapped_column(ForeignKey("rectificacion_logistica.id"))
    previo: Mapped[dict] = mapped_column(JSON, nullable=False)
    nuevo: Mapped[dict] = mapped_column(JSON, nullable=False)
    areas_delta: Mapped[list] = mapped_column(JSON, nullable=False)
    delta_total: Mapped[int] = mapped_column(Integer, nullable=False)
    delta_custodia: Mapped[int] = mapped_column(Integer, nullable=False)
    total_despues: Mapped[int] = mapped_column(Integer, nullable=False)
    custodia_despues: Mapped[int] = mapped_column(Integer, nullable=False)
    registrado_por: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    referencia_documento: Mapped[str] = mapped_column(String(200), nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
