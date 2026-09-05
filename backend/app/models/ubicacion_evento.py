from datetime import date

from sqlalchemy import String, Text, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class UbicacionEvento(Base):
    """
    Lugar físico externo o temporal donde puede estar un activo, separado
    del área organizacional responsable. Ejemplo: el área Cedoal es
    responsable del activo (custodia administrativa), pero el activo está
    físicamente en la Feria del Libro de La Paz del 5 al 15 de septiembre.

    Es opcional en 'movimiento': cuando el movimiento es solo interno entre
    áreas de la institución, ubicacion_evento_id queda en NULL.
    """

    __tablename__ = "ubicacion_evento"

    id: Mapped[int] = mapped_column(primary_key=True)
    area_responsable_id: Mapped[int] = mapped_column(ForeignKey("area.id"), nullable=False)
    nombre_lugar: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), default="externo")  # interno/externo/evento
    ciudad: Mapped[str | None] = mapped_column(String(100))
    provincia: Mapped[str | None] = mapped_column(String(100))
    departamento: Mapped[str | None] = mapped_column(String(100))
    pais: Mapped[str] = mapped_column(String(100), default="Bolivia")
    fecha_inicio: Mapped[date | None] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)
    observacion: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="activo")
