from datetime import date, datetime

from sqlalchemy import String, Text, ForeignKey, Numeric, Boolean, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DocumentoLegacy(Base):
    """Documento físico del Kardex histórico digitalizado (imagen fuente)."""

    __tablename__ = "documento_legacy"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_documento: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    periodo_documental: Mapped[str | None] = mapped_column(String(50))
    fecha_documento: Mapped[date | None] = mapped_column(Date)
    ruta_original: Mapped[str | None] = mapped_column(Text)
    checksum_original: Mapped[str | None] = mapped_column(String(128))
    estado: Mapped[str] = mapped_column(String(20), default="historico")
    observacion: Mapped[str | None] = mapped_column(Text)


class ExtraccionLegacy(Base):
    """Resultado del motor OCR/HTR (ej. TrOCR) sobre un documento legacy."""

    __tablename__ = "extraccion_legacy"

    id: Mapped[int] = mapped_column(primary_key=True)
    documento_legacy_id: Mapped[int] = mapped_column(ForeignKey("documento_legacy.id"), nullable=False)
    motor: Mapped[str] = mapped_column(String(100), nullable=False)
    modelo_version: Mapped[str | None] = mapped_column(String(100))
    texto_extraido: Mapped[str | None] = mapped_column(Text)
    confianza_global: Mapped[float | None] = mapped_column(Numeric(6, 5))
    procesado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    estado: Mapped[str] = mapped_column(String(20), default="activo")
    observacion: Mapped[str | None] = mapped_column(Text)


class ValidacionLegacy(Base):
    """Revisión humana (HITL) sobre una extracción OCR/HTR."""

    __tablename__ = "validacion_legacy"

    id: Mapped[int] = mapped_column(primary_key=True)
    extraccion_id: Mapped[int] = mapped_column(ForeignKey("extraccion_legacy.id"), nullable=False)
    validador_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    resultado: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_validacion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    observacion: Mapped[str | None] = mapped_column(Text)
    correccion_aplicada: Mapped[bool] = mapped_column(Boolean, default=False)
    estado: Mapped[str] = mapped_column(String(20), default="activo")
