from datetime import datetime
from sqlalchemy import ForeignKey, String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class DocumentoOperativo(Base):
    __tablename__ = 'documento_operativo'
    id: Mapped[int] = mapped_column(primary_key=True)
    articulo_id: Mapped[int] = mapped_column(ForeignKey('activo.id'), index=True)
    referencia: Mapped[str] = mapped_column(String(200))
    nombre: Mapped[str] = mapped_column(String(180))
    archivo: Mapped[str] = mapped_column(String(40), unique=True)
    tipo: Mapped[str] = mapped_column(String(50))
    bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    registrado_por: Mapped[int] = mapped_column(ForeignKey('usuario.id'))
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
