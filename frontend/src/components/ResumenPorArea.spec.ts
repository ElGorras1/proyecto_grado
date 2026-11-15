import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ResumenPorArea from './ResumenPorArea.vue'

describe('Resumen por área', () => {
  it('muestra los traslados del sentido elegido y abre su recorrido', async () => {
    const w = mount(ResumenPorArea, {
      props: {
        areas: [
          { id: 1, nombre: 'Archivo', entradas: 0, salidas: 8, custodia_actual: 3, alertas_abiertas: 1 },
          { id: 2, nombre: 'Depósito', entradas: 8, salidas: 0, custodia_actual: 0, alertas_abiertas: 0 },
        ],
        movimientos: [{
          id: 4, articulo: 'Cuaderno', articulo_id: 8, clase: 'TRANSFERENCIA',
          fecha_registro: '2026-04-01', cantidad_transferida: 8, area_origen_id: 1,
          area_destino_id: 2, documento: 'REF-04', estado: 'ACTIVO',
        }],
      },
      global: { stubs: { GrafoTrazabilidad: true, TrazabilidadArticulo: true } },
    })
    expect(w.text()).not.toContain('REF-04')
    await w.get('tbody button').trigger('click')
    expect(w.text()).toContain('REF-04')
    await w.get('.movimientos tbody button').trigger('click')
    expect(w.get('trazabilidad-articulo-stub').attributes('evento')).toBe('TRANSFERENCIA:4')
    await w.get('select').setValue('2')
    expect(w.text()).not.toContain('REF-04')
    w.unmount()
  })
})
