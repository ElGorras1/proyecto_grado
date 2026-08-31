from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, Numeric, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ResultadoRegla(Base):
    """Resultado de una regla determinística inmediata sobre un movimiento."""

    __tablename__ = "resultado_regla"

    id: Mapped[int] = mapped_column(primary_key=True)
    movimiento_id: Mapped[int] = mapped_column(ForeignKey("movimiento.id"), nullable=False)
    codigo_regla: Mapped[str] = mapped_column(String(80), nullable=False)
    resultado: Mapped[str] = mapped_column(String(20), nullable=False)  # cumple/advertencia/viola
    detalle: Mapped[str | None] = mapped_column(Text)
    evaluado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    estado: Mapped[str] = mapped_column(String(20), default="activo")


class EvaluacionAnomalia(Base):
    """Resultado de Isolation Forest (scikit-learn) sobre un movimiento."""

    __tablename__ = "evaluacion_anomalia"

    id: Mapped[int] = mapped_column(primary_key=True)
    movimiento_id: Mapped[int] = mapped_column(ForeignKey("movimiento.id"), nullable=False)
    modelo_version: Mapped[str] = mapped_column(String(100), nullable=False)
    ciclo_evaluacion: Mapped[str | None] = mapped_column(String(50))
    anomaly_score: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False)
    es_anomalia: Mapped[bool] = mapped_column(Boolean, nullable=False)
    umbral_aplicado: Mapped[float | None] = mapped_column(Numeric(12, 8))
    evaluado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    estado: Mapped[str] = mapped_column(String(20), default="activo")
