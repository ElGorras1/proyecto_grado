from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8)
    rol_id: int
    area_id: int | None = None


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    rol_id: int | None = None
    area_id: int | None = None


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol: str
    area_id: int | None = None
    estado: str
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("rol", mode="before")
    @classmethod
    def extract_rol_nombre(cls, v: Any) -> str:
        if hasattr(v, "nombre"):
            return v.nombre
        return str(v)


class CambiarPasswordRequest(BaseModel):
    password_nuevo: str = Field(..., min_length=8)


class RolOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None

    model_config = ConfigDict(from_attributes=True)
