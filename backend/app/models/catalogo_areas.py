"""Catálogo documental existente; no representa ubicaciones de existencias."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class CatalogoArea(Base):
    __tablename__ = "catalogo_areas"
    __table_args__ = (
        Index("uq_catalogo_nombre_normalizado", text("upper(trim(nombre_oficial))"), unique=True),
        Index("uq_catalogo_abrev_normalizada", text("upper(trim(abreviatura))"), unique=True),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_oficial: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    abreviatura: Mapped[str | None] = mapped_column(String(30))
    descripcion: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[str | None] = mapped_column(String(30), default="departamento", server_default="departamento")
    activa: Mapped[bool | None] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())


class SinonimoArea(Base):
    __tablename__ = "sinonimos_area"
    __table_args__ = (Index("uq_alias_texto_normalizado", text("upper(trim(texto_sucio))"), unique=True),)
    id: Mapped[int] = mapped_column(primary_key=True)
    texto_sucio: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    area_oficial_id: Mapped[int | None] = mapped_column(ForeignKey("catalogo_areas.id"))
    confirmado: Mapped[bool | None] = mapped_column(Boolean, default=False, server_default="false")
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())
