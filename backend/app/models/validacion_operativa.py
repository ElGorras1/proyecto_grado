"""Frozen audit samples for the operational anomaly model."""

from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class EstudioOperativo(Base):
    __tablename__ = "estudio_operativo"

    id: Mapped[int] = mapped_column(primary_key=True)
    modelo_id: Mapped[str] = mapped_column(ForeignKey("analitica_operativa_modelos.id"))
    creador_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    gestion: Mapped[int] = mapped_column()
    simulado: Mapped[bool] = mapped_column(Boolean)
    poblacion: Mapped[int] = mapped_column()
    semilla: Mapped[int] = mapped_column()
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class CotejoOperativo(Base):
    __tablename__ = "cotejo_operativo"
    __table_args__ = (
        UniqueConstraint("estudio_id", "resultado_id", name="uq_cotejo_operativo_resultado"),
        CheckConstraint("etiqueta IN ('ANOMALO', 'NORMAL', 'INDETERMINADO')", name="ck_cotejo_operativo_etiqueta"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    estudio_id: Mapped[int] = mapped_column(ForeignKey("estudio_operativo.id"), index=True)
    resultado_id: Mapped[int] = mapped_column(ForeignKey("analitica_operativa_resultados.id"))
    evidencia: Mapped[dict] = mapped_column(JSON)
    prediccion: Mapped[bool] = mapped_column(Boolean)
    etiqueta: Mapped[str | None] = mapped_column(String(20))
    motivo: Mapped[str | None] = mapped_column(Text)
    respaldo: Mapped[str | None] = mapped_column(String(250))
    revisor_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    revisado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
