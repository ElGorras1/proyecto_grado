from datetime import date, datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator


class FilaKardex(BaseModel):
    fecha: date | None = Field(default=None,
        description="Fecha completa acreditada por la celda, YYYY-MM-DD. Devuelve null si está vacía, parcial o ilegible. Nunca completes día, mes o año por secuencia."
    )
    fecha_documental_texto: str | None = Field(default=None, max_length=100,
        description="Texto de la celda FECHA tal como está escrito, aunque sea parcial. null si está vacía.")
    fecha_precision: Literal["COMPLETA", "PARCIAL", "AUSENTE", "ILEGIBLE"] | None = None
    detalle: str = Field(
        description="Texto exacto de la columna DETALLE. Limpia espacios extra pero conserva el significado. No modifiques nombres de ferias ni descripciones."
    )
    referencia: Optional[str] = Field(
        default=None,
        description="Texto de la columna REF. o documento de respaldo. Si está vacío devuelve null.",
    )
    area: Optional[str] = Field(
        default=None, description="Texto de la columna AREA. Si está vacío devuelve null."
    )
    ingresos: Optional[int] = Field(
        default=None,
        description="Número en la columna INGRESOS. Si está vacía o tiene un guión, devuelve null.",
    )
    salidas: Optional[int] = Field(
        default=None,
        description="Número en la columna SALIDAS. Si está vacía o tiene un guión, devuelve null.",
    )
    saldo_registrado: int = Field(description="Número en la columna SALDO. Es obligatorio.")
    orden_fila: int = Field(
        description="Posición visual de la fila en la tabla de la hoja (1, 2, 3...)."
    )

    @model_validator(mode="after")
    def conservar_fecha_documental(self):
        self.fecha_precision = self.fecha_precision or ("COMPLETA" if self.fecha else "AUSENTE")
        if self.fecha_precision == "COMPLETA" and self.fecha is None:
            raise ValueError("Una fecha completa requiere día, mes y año acreditados")
        if self.fecha_precision != "COMPLETA" and self.fecha is not None:
            raise ValueError("Una fecha parcial, ausente o ilegible debe conservar fecha=null")
        if self.fecha_precision == "PARCIAL" and not (self.fecha_documental_texto or "").strip():
            raise ValueError("Conserva el texto de la fecha parcial")
        if self.fecha_precision == "AUSENTE" and (self.fecha_documental_texto or "").strip():
            raise ValueError("Una celda con texto requiere precisión parcial o ilegible")
        return self


class ExtraccionKardexHoja(BaseModel):
    nombre_articulo: str = Field(
        description="Nombre del artículo o producto que aparece en el encabezado de la hoja de kárdex (ej: 'MUSICA CHAPACA CD')."
    )
    filas: List[FilaKardex] = Field(
        description="Lista de todos los movimientos de la tabla de kárdex en orden estricto de arriba hacia abajo."
    )


class LoteCargaCreate(BaseModel):
    total_imagenes: int


class MovimientoKardexCreate(BaseModel):
    articulo_id: int
    lote_id: Optional[int] = None
    fecha_movimiento: date | None = None
    fecha_documental_texto: str | None = Field(default=None, max_length=100)
    fecha_precision: Literal["COMPLETA", "PARCIAL", "AUSENTE", "ILEGIBLE"] | None = None
    detalle: str
    referencia: Optional[str] = None
    area: Optional[str] = None
    ingresos: Optional[int] = None
    salidas: Optional[int] = None
    saldo_registrado: int
    ruta_imagen_respaldo: Optional[str] = None
    numero_pagina: Optional[int] = None
    orden_fila: Optional[int] = None
    orden_pagina_validado: Optional[int] = None
    revision_documental: Optional[dict] = None
    tiene_error_saldo: bool = False
    fecha_original: Optional[date] = None
    datos_originales: Optional[dict] = None
    tiene_error_fecha: bool = False
    fecha_estado: str = "SIN_ALERTA"
    saldo_calculado: Optional[int] = None
    observaciones: Optional[str] = None
    nodo_grafo: Optional[str] = None
    requiere_auditoria_nodo: bool = False
    area_estado: str = "PENDIENTE_HIL"
    referencia_estado: str = "AUSENTE"
    requiere_auditoria_referencia: bool = False
    # Transacciones modernas
    usuario_operador: Optional[str] = None
    encargado_id: Optional[int] = None
    usuario_registrador_id: Optional[int] = None
    encargado_nombre: Optional[str] = None
    registrado_en: Optional[datetime] = None
    ocurrido_en: Optional[datetime] = None
    solicitud_id: Optional[str] = None
    alertas_control: Optional[list[dict]] = None
    justificacion_alertas: Optional[str] = None
    tipo_operacion: Optional[str] = None
    receptor: Optional[str] = None
    receptor_tipo: Optional[str] = None
    area_operativa_id: Optional[int] = None
    feria_id: Optional[int] = None
    ciudad_feria: Optional[str] = None
    canal_venta: Optional[str] = None
    motivo_baja: Optional[str] = None
    referencia_documento: Optional[str] = None
    movimiento_origen_id: Optional[int] = None
    devuelto_por: Optional[str] = None
    corrige_movimiento_id: Optional[int] = None
    cantidad_anterior: Optional[int] = None
    cantidad_corregida: Optional[int] = None
    motivo_correccion: Optional[str] = None
    autorizado_por_id: Optional[int] = None
    estado: str = "ACTIVO"


class MovimientoKardexOut(MovimientoKardexCreate):
    id: int
    tanda: Optional[int] = Field(default=None, ge=1, le=9999)
    tratamiento_hil: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("revision_documental")
    def revision_vigente(self, revision: dict | None):
        # La cadena completa permanece en la BD y en el historial de revisiones.
        # Repetirla en cada fila de un listado aumenta el tráfico sin aportar
        # información a la lectura vigente de la hoja.
        if revision is None:
            return None
        return {k: v for k, v in revision.items() if k != "revision_previa_enmienda_focalizada"}


class MovimientoKardexEdit(BaseModel):
    ingresos: Optional[int] = Field(None, ge=0)
    salidas: Optional[int] = Field(None, ge=0)
    saldo_registrado: int
    nodo_grafo: Optional[str] = None
    requiere_auditoria_nodo: Optional[bool] = None
    area_estado: Optional[Literal["RESUELTA_AUTOMATICAMENTE", "RESUELTA_POR_HUMANO", "SIN_AREA_REGISTRADA", "NO_APLICA", "AREA_NO_CATALOGADA", "PENDIENTE_HIL"]] = None
    referencia_estado: Optional[Literal["PRESENTE", "AUSENTE", "ILEGIBLE", "INCIERTA"]] = None
    requiere_auditoria_referencia: Optional[bool] = None
    fecha_movimiento: Optional[date] = None
    decision_fecha: Optional[Literal["corregir", "confirmar_documento", "ausente", "parcial", "ilegible"]] = None
    fecha_documental_texto: str | None = Field(default=None, max_length=100)
    origen_fecha: Optional[Literal["FOTO", "HIPOTESIS", "SECUENCIA_AJUSTADA"]] = None
    motivo: str = Field(default="", max_length=1000)
    referencia: Optional[str] = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validar_decision_fecha(self):
        if self.decision_fecha == "corregir" and self.fecha_movimiento is None:
            raise ValueError("Indica la fecha corregida")
        if self.fecha_movimiento is not None and self.decision_fecha != "corregir":
            raise ValueError("Cambiar una fecha requiere la decisión corregir")
        if self.origen_fecha is not None and self.decision_fecha != "corregir":
            raise ValueError("El origen de fecha requiere la decisión corregir")
        if self.decision_fecha == "parcial" and not (self.fecha_documental_texto or "").strip():
            raise ValueError("Conserva el texto escrito de la fecha parcial")
        if self.decision_fecha == "ausente" and (self.fecha_documental_texto or "").strip():
            raise ValueError("Una fecha con texto no es una celda ausente")
        if self.fecha_documental_texto is not None and self.decision_fecha not in {"corregir", "parcial", "ilegible", "ausente"}:
            raise ValueError("El texto de fecha requiere una decisión documental")
        return self
