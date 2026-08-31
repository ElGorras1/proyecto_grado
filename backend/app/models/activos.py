from datetime import date

from sqlalchemy import String, Text, ForeignKey, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CategoriaActivo(Base):
    __tablename__ = "categoria_activo"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    codigo: Mapped[str | None] = mapped_column(String(30), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    estado: Mapped[str] = mapped_column(String(20), default="activo")


class Activo(Base):
    __tablename__ = "activo"

    id: Mapped[int] = mapped_column(primary_key=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria_activo.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    unidad_medida: Mapped[str] = mapped_column(String(30), default="unidad")
    estado: Mapped[str] = mapped_column(String(20), default="activo")
    fecha_alta: Mapped[date | None] = mapped_column(Date)
    fecha_baja: Mapped[date | None] = mapped_column(Date)


class Existencia(Base):
    __tablename__ = "existencia"

    id: Mapped[int] = mapped_column(primary_key=True)
    activo_id: Mapped[int] = mapped_column(ForeignKey("activo.id"), nullable=False)
    area_id: Mapped[int] = mapped_column(ForeignKey("area.id"), nullable=False)
    cantidad: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    stock_minimo: Mapped[float | None] = mapped_column(Numeric(14, 2))
    stock_maximo: Mapped[float | None] = mapped_column(Numeric(14, 2))
    estado: Mapped[str] = mapped_column(String(20), default="activo")
