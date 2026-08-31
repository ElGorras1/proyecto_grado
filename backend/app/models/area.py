from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Area(Base):
    __tablename__ = "area"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    codigo: Mapped[str | None] = mapped_column(String(30), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    estado: Mapped[str] = mapped_column(String(20), default="activo")

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="area")  # noqa: F821
