export type ClaseLogistica = 'TRANSFERENCIA' | 'ENTREGA' | 'EVENTO_CUSTODIA'
export interface DatosLogisticos {
  cantidad: number; encargado_id: number; referencia_documento: string; observaciones: string
  area_origen_id?: number; area_destino_id?: number | null
  tipo?: 'FERIA' | 'CONSIGNACION' | 'VENTA' | 'RETORNO'
  receptor_nombre?: string; receptor_tipo?: string; ubicacion_externa?: string
  ciudad?: string | null; comprador?: string | null
}
export interface RectificableLogistico {
  id: number; version_rectificacion?: string; datos_vigentes?: DatosLogisticos
}
export interface FuenteLogistica {
  clase: ClaseLogistica; registro_id: number; version: string; datos: DatosLogisticos
}
