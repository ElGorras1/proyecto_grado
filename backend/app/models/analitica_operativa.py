"""Versiones y puntuaciones de operaciones digitales, separadas del OCR."""

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ModeloOperativo(Base):
    __tablename__ = "analitica_operativa_modelos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    estado: Mapped[str] = mapped_column(String(24), nullable=False)
    plaza: Mapped[int | None] = mapped_column(Integer, unique=True)
    activo: Mapped[int | None] = mapped_column(Integer, unique=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    configuracion: Mapped[dict] = mapped_column(JSON, nullable=False)
    corte: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    huella: Mapped[str] = mapped_column(String(64), nullable=False)
    metricas: Mapped[dict | None] = mapped_column(JSON)
    umbral: Mapped[float | None] = mapped_column(Float)
    artefacto_sha256: Mapped[str | None] = mapped_column(String(64))
    error: Mapped[str | None] = mapped_column(Text)


class ResultadoOperativo(Base):
    __tablename__ = "analitica_operativa_resultados"
    __table_args__ = (
        UniqueConstraint("modelo_id", "recurso", name="uq_resultado_operativo_recurso"),
        CheckConstraint(
            "(CASE WHEN movimiento_id IS NULL THEN 0 ELSE 1 END + "
            "CASE WHEN transferencia_id IS NULL THEN 0 ELSE 1 END + "
            "CASE WHEN custodia_id IS NULL THEN 0 ELSE 1 END + "
            "CASE WHEN evento_custodia_id IS NULL THEN 0 ELSE 1 END) = 1",
            name="ck_resultado_operativo_origen",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    modelo_id: Mapped[str] = mapped_column(ForeignKey("analitica_operativa_modelos.id"), index=True)
    recurso: Mapped[str] = mapped_column(String(70), nullable=False)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), index=True)
    movimiento_id: Mapped[int | None] = mapped_column(ForeignKey("movimientos_kardex.id"))
    transferencia_id: Mapped[int | None] = mapped_column(ForeignKey("transferencia_area.id"))
    custodia_id: Mapped[int | None] = mapped_column(ForeignKey("custodia_externa.id"))
    evento_custodia_id: Mapped[int | None] = mapped_column(ForeignKey("evento_custodia_externa.id"))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    contexto: Mapped[dict] = mapped_column(JSON, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    alerta: Mapped[bool] = mapped_column(nullable=False)
