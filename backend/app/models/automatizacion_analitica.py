"""Seguimiento automático separado de los cortes y resultados de evaluación."""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class PoliticaAnalitica(Base):
    __tablename__ = "politica_analitica"
    __table_args__ = (
        CheckConstraint("id=1", name="ck_politica_analitica_unica"),
        CheckConstraint("gestion_hasta BETWEEN 1900 AND 9998", name="ck_politica_gestion"),
        CheckConstraint("intervalo_segundos BETWEEN 60 AND 86400", name="ck_politica_intervalo"),
        CheckConstraint("revision_dias BETWEEN 1 AND 365", name="ck_politica_revision"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    modelo_base_id: Mapped[str] = mapped_column(ForeignKey("analitica_modelos.id"), nullable=False)
    habilitada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    preparar_candidatos: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    gestion_hasta: Mapped[int] = mapped_column(Integer, nullable=False, default=2025)
    intervalo_segundos: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    revision_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    ultimo_analisis: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultima_revision: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultimo_informe: Mapped[dict | None] = mapped_column(JSON)
    ultimo_error: Mapped[str | None] = mapped_column(Text)
    candidato_id: Mapped[str | None] = mapped_column(ForeignKey("analitica_modelos.id"))
    huella_revision: Mapped[str | None] = mapped_column(String(64))


class ResultadoSeguimiento(Base):
    __tablename__ = "resultado_seguimiento"
    __table_args__ = (
        UniqueConstraint(
            "modelo_id", "movimiento_id", "huella_snapshot", name="uq_seguimiento_version"
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    modelo_id: Mapped[str] = mapped_column(ForeignKey("analitica_modelos.id"), nullable=False)
    movimiento_id: Mapped[int] = mapped_column(
        ForeignKey("movimientos_kardex.id"), nullable=False, index=True
    )
    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), nullable=False, index=True)
    gestion: Mapped[int] = mapped_column(Integer, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    huella_snapshot: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    contexto: Mapped[dict] = mapped_column(JSON, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    alerta: Mapped[bool] = mapped_column(Boolean, nullable=False)
    estado_revision: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDIENTE")
    revision_numero: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    etiqueta: Mapped[str | None] = mapped_column(String(30))


class RevisionSeguimiento(Base):
    __tablename__ = "revision_seguimiento"
    id: Mapped[int] = mapped_column(primary_key=True)
    resultado_id: Mapped[int] = mapped_column(
        ForeignKey("resultado_seguimiento.id"), nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    anterior: Mapped[str] = mapped_column(String(30), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False)
    etiqueta: Mapped[str] = mapped_column(String(30), nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
