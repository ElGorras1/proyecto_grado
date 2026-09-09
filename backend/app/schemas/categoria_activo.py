from pydantic import BaseModel, ConfigDict, Field


class CategoriaActivoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    codigo: str | None = Field(default=None, max_length=30)
    descripcion: str | None = Field(default=None, max_length=255)


class CategoriaActivoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    codigo: str | None = Field(default=None, max_length=30)
    descripcion: str | None = Field(default=None, max_length=255)


class CategoriaActivoOut(BaseModel):
    id: int
    nombre: str
    codigo: str | None = None
    descripcion: str | None = None
    estado: str

    model_config = ConfigDict(from_attributes=True)
