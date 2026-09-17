from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

class FilaKardex(BaseModel):
    fecha: date = Field(description="Fecha del movimiento en formato YYYY-MM-DD. Si el año tiene 2 dígitos (ej 10) conviértelo al siglo correspondiente (2010).")
    detalle: str = Field(description="Texto exacto de la columna DETALLE. Limpia espacios extra pero conserva el significado. No modifiques nombres de ferias ni descripciones.")
    referencia: Optional[str] = Field(default=None, description="Texto de la columna REF. o documento de respaldo. Si está vacío devuelve null.")
    area: Optional[str] = Field(default=None, description="Texto de la columna AREA. Si está vacío devuelve null.")
    ingresos: Optional[int] = Field(default=None, description="Número en la columna INGRESOS. Si está vacía o tiene un guión, devuelve null.")
    salidas: Optional[int] = Field(default=None, description="Número en la columna SALIDAS. Si está vacía o tiene un guión, devuelve null.")
    saldo_registrado: int = Field(description="Número en la columna SALDO. Es obligatorio.")
    orden_fila: int = Field(description="Posición visual de la fila en la tabla de la hoja (1, 2, 3...).")

class ExtraccionKardexHoja(BaseModel):
    nombre_articulo: str = Field(description="Nombre del artículo o producto que aparece en el encabezado de la hoja de kárdex (ej: 'MUSICA CHAPACA CD').")
    filas: List[FilaKardex] = Field(description="Lista de todos los movimientos de la tabla de kárdex en orden estricto de arriba hacia abajo.")

class LoteCargaCreate(BaseModel):
    total_imagenes: int

class MovimientoKardexCreate(BaseModel):
    articulo_id: int
    lote_id: Optional[int] = None
    fecha_movimiento: date
    detalle: str
    referencia: Optional[str] = None
    area: Optional[str] = None
    ingresos: Optional[int] = None
    salidas: Optional[int] = None
    saldo_registrado: int
    ruta_imagen_respaldo: Optional[str] = None
    numero_pagina: Optional[int] = None
    orden_fila: Optional[int] = None
    tiene_error_saldo: bool = False
    saldo_calculado: Optional[int] = None
    observaciones: Optional[str] = None
    nodo_grafo: Optional[str] = None
    requiere_auditoria_nodo: bool = False
    # Transacciones modernas
    usuario_operador: Optional[str] = None
    tipo_operacion: Optional[str] = None
    receptor: Optional[str] = None
    feria_id: Optional[int] = None
    ciudad_feria: Optional[str] = None
    canal_venta: Optional[str] = None
    motivo_baja: Optional[str] = None
    referencia_documento: Optional[str] = None
    estado: str = "ACTIVO"

class MovimientoKardexOut(MovimientoKardexCreate):
    id: int
    class Config:
        from_attributes = True

class MovimientoKardexEdit(BaseModel):
    ingresos: Optional[int] = None
    salidas: Optional[int] = None
    saldo_registrado: int
    nodo_grafo: Optional[str] = None
    requiere_auditoria_nodo: Optional[bool] = None
