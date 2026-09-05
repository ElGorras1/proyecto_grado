from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditoriaAccesoOut(BaseModel):
    """Schema de respuesta para el reporte de accesos (login)."""

    id: int
    usuario_id: int | None = None
    resultado: str
    fecha_hora: datetime
    ip_origen: str | None = None
    detalle: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)
