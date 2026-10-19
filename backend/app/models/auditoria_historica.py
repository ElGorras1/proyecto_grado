"""Analítica aditiva: nunca actualiza el ledger ni las evidencias."""

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
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


def ahora():
    return datetime.now(UTC)


class ModeloHistorico(Base):
    __tablename__ = "analitica_modelos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    estado: Mapped[str] = mapped_column(String(24), nullable=False)
    # Una única plaza, liberada al terminar; múltiples NULL permitidos.
    plaza: Mapped[int | None] = mapped_column(Integer, unique=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    terminado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    configuracion: Mapped[dict] = mapped_column(JSON, nullable=False)
    corte: Mapped[dict] = mapped_column(JSON, nullable=False)
    huella: Mapped[str] = mapped_column(String(64), nullable=False)
    metricas: Mapped[dict | None] = mapped_column(JSON)
    umbral: Mapped[float | None] = mapped_column(Float)
    artefacto_sha256: Mapped[str | None] = mapped_column(String(64))
    error: Mapped[str | None] = mapped_column(Text)


class ResultadoHistorico(Base):
    __tablename__ = "analitica_resultados"
    __table_args__ = (
        UniqueConstraint("modelo_id", "movimiento_id", name="uq_analitica_modelo_movimiento"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    modelo_id: Mapped[str] = mapped_column(ForeignKey("analitica_modelos.id"), index=True)
    movimiento_id: Mapped[int] = mapped_column(ForeignKey("movimientos_kardex.id"), index=True)
    gestion: Mapped[int] = mapped_column(Integer, index=True)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), index=True)
    nodo: Mapped[str | None] = mapped_column(String(100))
    score: Mapped[float] = mapped_column(Float)
    alerta: Mapped[bool] = mapped_column(Boolean, index=True)
    particion: Mapped[str] = mapped_column(String(20))
    muestra_control: Mapped[bool] = mapped_column(Boolean, default=False)
    snapshot: Mapped[dict] = mapped_column(JSON)
    contexto: Mapped[dict] = mapped_column(JSON)
    estado_revision: Mapped[str] = mapped_column(String(30), default="PENDIENTE")
    revision_numero: Mapped[int] = mapped_column(Integer, default=0)
    etiqueta: Mapped[str | None] = mapped_column(String(30))


class RevisionHistorica(Base):
    __tablename__ = "analitica_revisiones"
    id: Mapped[int] = mapped_column(primary_key=True)
    resultado_id: Mapped[int] = mapped_column(ForeignKey("analitica_resultados.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    anterior: Mapped[str] = mapped_column(String(30))
    estado: Mapped[str] = mapped_column(String(30))
    motivo: Mapped[str] = mapped_column(Text)
    etiqueta: Mapped[str | None] = mapped_column(String(30))
