"""Declaraciones humanas de cobertura; los escaneos observados se calculan aparte."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CoberturaArticulo(Base):
    __tablename__ = "cobertura_articulo"
    __table_args__ = (CheckConstraint(
        "estado IN ('SIN_CONFIRMAR', 'PARCIAL', 'CIERRE_CONFIRMADO')",
        name="ck_cobertura_articulo_estado"),)

    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), primary_key=True)
    estado: Mapped[str] = mapped_column(String(24), nullable=False)
    referencia: Mapped[str] = mapped_column(String(255), nullable=False)
    observacion: Mapped[str] = mapped_column(Text, nullable=False)
    ultimo_lote_revisado_id: Mapped[int | None] = mapped_column(Integer)
    revisado_por: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    revisado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TramoCobertura(Base):
    __tablename__ = "tramo_cobertura"
    __table_args__ = (
        CheckConstraint("gestion_desde <= gestion_hasta", name="ck_tramo_periodo"),
        CheckConstraint("estado IN ('PENDIENTE', 'SIN_CONFIRMAR', 'CONFIRMADO')",
                        name="ck_tramo_estado"),
        CheckConstraint("paginas_faltantes IS NULL OR paginas_faltantes >= 0",
                        name="ck_tramo_paginas_faltantes"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), nullable=False, index=True)
    gestion_desde: Mapped[int] = mapped_column(Integer, nullable=False)
    gestion_hasta: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    paginas_faltantes: Mapped[int | None] = mapped_column(Integer)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    referencia: Mapped[str] = mapped_column(String(255), nullable=False)
    revisado_por: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    revisado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
