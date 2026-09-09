from pydantic import BaseModel, ConfigDict


class ItemReporteInventario(BaseModel):
    existencia_id: int
    activo_id: int
    activo_codigo: str
    activo_nombre: str
    categoria_id: int
    categoria_nombre: str
    area_id: int
    area_nombre: str
    cantidad: float
    stock_minimo: float | None = None
    stock_maximo: float | None = None
    unidad_medida: str
    stock_bajo: bool
    estado: str

    model_config = ConfigDict(from_attributes=True)
