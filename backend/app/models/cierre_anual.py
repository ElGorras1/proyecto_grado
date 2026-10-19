"""Cierres digitales versionados: el snapshot no se reescribe al reabrir."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CierreAnual(Base):
    __tablename__ = "cierre_anual"
    __table_args__ = (
        UniqueConstraint("gestion", "version", name="uq_cierre_anual_version"),
        CheckConstraint("estado IN ('CERRADO','REABIERTO')", name="ck_cierre_anual_estado"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    solicitud_id: Mapped[str] = mapped_column(String(36), unique=True)
    solicitud_huella: Mapped[str] = mapped_column(String(64), nullable=False)
    gestion: Mapped[int] = mapped_column(Integer, index=True)
    gestion_activa: Mapped[int | None] = mapped_column(Integer, unique=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    huella: Mapped[str] = mapped_column(String(64), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    documento: Mapped[str] = mapped_column(String(200), nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    reabierto_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    reabierto_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_reapertura: Mapped[str | None] = mapped_column(Text)
