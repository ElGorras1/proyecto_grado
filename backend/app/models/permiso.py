from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Permiso(Base):
    __tablename__ = "permiso"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    codigo: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255))
    estado: Mapped[str] = mapped_column(String(20), default="activo")

    roles: Mapped[list["Rol"]] = relationship(  # noqa: F821
        secondary="rol_permiso", back_populates="permisos"
    )
