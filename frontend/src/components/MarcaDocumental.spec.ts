import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import MarcaDocumental from './MarcaDocumental.vue'

describe('Procedencia del área normalizada', () => {
  it('distingue el área inferida de la lectura conservada', () => {
    const w = mount(MarcaDocumental, { props: { revision: { asignacion_area: {
      estado: 'INFERIDA', area: 'Capacitación', literal: 'CDP', motivo: 'Parecido y contexto del artículo.', soporte: 'MEDIO',
    } } } })
    expect(w.text()).toContain('área inferida: Capacitación')
    expect(w.text()).toContain('Lectura conservada: CDP')
    expect(w.text()).toContain('identidad institucional sigue por confirmar')
  })
  it('no presenta como vigente una inferencia sustituida por revisión manual', () => {
    const w = mount(MarcaDocumental, { props: { revision: { asignacion_area: {
      estado: 'SUSTITUIDA_REVISION_MANUAL', area: 'Capacitación', literal: 'CDP', motivo: 'Anterior', soporte: 'MEDIO',
    } } } })
    expect(w.text()).not.toContain('área inferida:')
  })
})
