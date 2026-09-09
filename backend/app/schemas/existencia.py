from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExistenciaCreate(BaseModel):
    activo_id: int
    area_id: int
    cantidad: float = Field(default=0, ge=0)
    stock_minimo: float | None = Field(default=None, ge=0)
    stock_maximo: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validar_rango_stock(self) -> "ExistenciaCreate":
        if self.stock_minimo is not None and self.stock_maximo is not None:
            if self.stock_maximo < self.stock_minimo:
                raise ValueError("El stock máximo debe ser mayor o igual al stock mínimo")
        return self


class ExistenciaUpdate(BaseModel):
    cantidad: float | None = Field(default=None, ge=0)
    stock_minimo: float | None = Field(default=None, ge=0)
    stock_maximo: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validar_rango_stock(self) -> "ExistenciaUpdate":
        if self.stock_minimo is not None and self.stock_maximo is not None:
            if self.stock_maximo < self.stock_minimo:
                raise ValueError("El stock máximo debe ser mayor o igual al stock mínimo")
        return self


class ExistenciaOut(BaseModel):
    id: int
    activo_id: int
    area_id: int
    activo_nombre: str | None = None
    activo_codigo: str | None = None
    area_nombre: str | None = None
    area_codigo: str | None = None
    cantidad: float
    stock_minimo: float | None = None
    stock_maximo: float | None = None
    estado: str

    model_config = ConfigDict(from_attributes=True)
