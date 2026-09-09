from datetime import date
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ActivoCreate(BaseModel):
    categoria_id: int
    codigo: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=150)
    descripcion: str | None = None
    unidad_medida: str = Field(default="unidad", max_length=30)
    fecha_alta: date | None = None
    fecha_baja: date | None = None

    @model_validator(mode="after")
    def validar_fechas(self) -> "ActivoCreate":
        if self.fecha_alta and self.fecha_baja and self.fecha_baja < self.fecha_alta:
            raise ValueError("La fecha de baja no puede ser anterior a la fecha de alta")
        return self


class ActivoUpdate(BaseModel):
    categoria_id: int | None = None
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    descripcion: str | None = None
    unidad_medida: str | None = Field(default=None, max_length=30)
    fecha_alta: date | None = None
    fecha_baja: date | None = None

    @model_validator(mode="after")
    def validar_fechas(self) -> "ActivoUpdate":
        if self.fecha_alta and self.fecha_baja and self.fecha_baja < self.fecha_alta:
            raise ValueError("La fecha de baja no puede ser anterior a la fecha de alta")
        return self


class ActivoOut(BaseModel):
    id: int
    categoria_id: int
    categoria_nombre: str | None = None
    codigo: str
    nombre: str
    descripcion: str | None = None
    unidad_medida: str
    estado: str
    fecha_alta: date | None = None
    fecha_baja: date | None = None

    model_config = ConfigDict(from_attributes=True)
