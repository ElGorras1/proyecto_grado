export const categoriasHil = {
  DISCREPANCIA_DOCUMENTAL: 'Discrepancia del documento',
  AMBITO_DOCUMENTAL_INCIERTO: 'Ámbito de la hoja no confirmado',
  DEPENDENCIA_OTRA_FILA: 'Depende de otra fila',
  POSIBLE_DUPLICIDAD_DOCUMENTAL: 'Operaciones parecidas conservadas',
  CATALOGO_NO_CONFIRMADO: 'Nombre o sigla sin equivalencia confirmada',
  LECTURA_INCIERTA: 'Lectura no inequívoca',
  MARCA_NO_INTERPRETADA: 'Marca del papel conservada',
  EFECTO_INDETERMINADO: 'Efecto del movimiento no acreditado',
} as const

export interface TratamientoHil {
  estado: 'POR_CATEGORIZAR' | 'SIN_AVISOS' | 'REQUIERE_RECATEGORIZAR' | 'CATEGORIZADO_CON_MARCA'
  etiqueta: string
  categorias: string[]
  decisiones: { campo: string; categoria: string; etiqueta: string; motivo: string; criterios: string[] }[]
  datos_confirmados: boolean
  habilita_entrenamiento: boolean
  autor?: string
  categorizado_en?: string
}
