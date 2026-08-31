from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    rol_id: Mapped[int] = mapped_column(ForeignKey("rol.id"), nullable=False)
    area_id: Mapped[int | None] = mapped_column(ForeignKey("area.id"))
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="activo")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rol: Mapped["Rol"] = relationship(back_populates="usuarios")  # noqa: F821
    area: Mapped["Area"] = relationship(back_populates="usuarios")  # noqa: F821
