from sqlalchemy import String, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Area(Base):
    __tablename__ = "area"
    __table_args__ = (
        Index("uq_area_nombre_normalizado", text("upper(trim(nombre))"), unique=True),
        Index("uq_area_codigo_normalizado", text("upper(trim(codigo))"), unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    codigo: Mapped[str | None] = mapped_column(String(30), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    estado: Mapped[str] = mapped_column(String(20), default="activo")

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="area")  # noqa: F821
