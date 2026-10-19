import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import EvaluacionAnalitica from './EvaluacionAnalitica.vue'
import type { DiagnosticoAnalitica, ProgresoEvaluacion } from '@/services/analitica'

function datos(): DiagnosticoAnalitica {
  const progreso: ProgresoEvaluacion = {
    k: 20,
    disponibles: 20,
    revisados_concluyentes: 19,
    relevantes: 19,
    pendientes: 1,
    errores_documentales: 1,
    no_concluyentes: 0,
    sin_resultado: 0,
    ids_duplicados: 0,
    seleccion_integra: true,
    precision_at_k: null,
  }
  return {
    version: 1,
    modelo_id: 'modelo-1',
    estado: 'CONSISTENTE',
    comprobaciones: [
      {
        codigo: 'separacion',
        titulo: 'Lotes separados',
        estado: 'OK',
        detalle: '0 fugas',
        ejemplos: [],
      },
    ],
    reproduccion_artefacto: 'NO_VERIFICADO',
    cobertura: {
      evaluados: 200,
      evaluacion: 40,
      sin_referencia_propia: 28,
      porcentaje_sin_referencia: 70,
      regla_sin_referencia_top: 0,
    },
    evaluacion: {
      modelo: { ...progreso },
      regla: { ...progreso },
      control: { ...progreso },
      advertencia: '',
    },
  }
}

describe('Evaluación independiente', () => {
  it('separa comprobación técnica de precisión pendiente y muestra los errores documentales', () => {
    const w = mount(EvaluacionAnalitica, { props: { diagnostico: datos(), cargando: false } })
    expect(w.text()).toContain('Esto todavía no demuestra precisión')
    expect(w.text()).toContain('19/20')
    expect(w.text()).toContain('1 con error documental')
    expect(w.text()).toContain('(70.0%)')
    expect(w.text()).not.toContain('95.0%')
    expect(w.text()).toContain('Pendiente')
  })
  it('solo muestra proporción para una selección íntegra y oculta métricas cuando hay inconsistencias', async () => {
    const d = datos()
    d.evaluacion.modelo.precision_at_k = 0.95
    const w = mount(EvaluacionAnalitica, { props: { diagnostico: d, cargando: false } })
    expect(w.text()).toContain('95.0%')
    await w.setProps({ diagnostico: { ...d, estado: 'INCONSISTENTE' } })
    expect(w.get('[role="alert"]').text()).toContain('inconsistencias')
    expect(w.text()).not.toContain('95.0%')
  })
  it('abre cada selección y evita acciones durante la carga', async () => {
    const w = mount(EvaluacionAnalitica, { props: { diagnostico: datos(), cargando: false } })
    for (const b of w.findAll('button')) await b.trigger('click')
    expect(w.emitted('seleccionar')).toEqual([['top_modelo'], ['top_regla'], ['control']])
    await w.setProps({ cargando: true })
    expect(w.findAll('button').every((b) => b.attributes('disabled') !== undefined)).toBe(true)
  })
})
