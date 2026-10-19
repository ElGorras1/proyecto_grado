export interface ProgresoEvaluacion {
  k: number
  disponibles: number
  revisados_concluyentes: number
  relevantes: number
  pendientes: number
  errores_documentales: number
  no_concluyentes: number
  sin_resultado: number
  ids_duplicados: number
  seleccion_integra: boolean
  precision_at_k: number | null
}

export interface DiagnosticoAnalitica {
  version: number
  modelo_id: string
  estado: 'CONSISTENTE' | 'INCONSISTENTE' | 'NO_VERIFICADO'
  comprobaciones: {
    codigo: string
    titulo: string
    estado: 'OK' | 'FALLO'
    detalle: string
    ejemplos: (number | string)[]
  }[]
  reproduccion_artefacto: string
  cobertura: {
    evaluados: number
    evaluacion: number
    sin_referencia_propia: number
    porcentaje_sin_referencia: number | null
    regla_sin_referencia_top: number
  }
  evaluacion: Record<'modelo' | 'regla' | 'control', ProgresoEvaluacion> & { advertencia: string }
}
