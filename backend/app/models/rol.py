from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Rol(Base):
    __tablename__ = "rol"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    estado: Mapped[str] = mapped_column(String(20), default="activo")

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")  # noqa: F821
    permisos: Mapped[list["Permiso"]] = relationship(  # noqa: F821
        secondary="rol_permiso", back_populates="roles"
    )
