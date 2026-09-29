import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RevisionHil from './RevisionHil.vue'
import api from '@/services/api'
vi.mock('@/services/api', () => ({ default: { get: vi.fn(), put: vi.fn(), defaults: { baseURL: 'http://localhost:8000/api/v1' } } }))
const m = { id: 7, fecha_movimiento: '2025-01-01', fecha_original: '2025-01-01', fecha_estado: 'PENDIENTE_HIL',
  ingresos: null, salidas: 2, saldo_registrado: 8, detalle: 'Salida', referencia: null, area: null,
  nodo_grafo: 'Ventas', referencia_estado: 'AUSENTE', ruta_imagen_respaldo: 'storage/pagina.webp' }
beforeEach(() => { vi.resetAllMocks(); vi.mocked(api.get).mockResolvedValue({ data: [] }); vi.mocked(api.put).mockResolvedValue({ data: {} }) })

describe('Revisión HIL auditable', () => {
  it('no guarda sin motivo y confirma la fecha sin reemplazarla', async () => {
    const w = mount(RevisionHil, { props: { movimiento: m } }); await flushPromises()
    await w.find('form').trigger('submit'); expect(api.put).not.toHaveBeenCalled()
    expect(w.find('[role="alert"]').text()).toContain('motivo')
    await w.find('textarea').setValue('La fotografía confirma la fecha escrita')
    await w.find('select').setValue('confirmar_documento')
    await w.find('form').trigger('submit'); await flushPromises()
    const datos = vi.mocked(api.put).mock.calls[0][1] as Record<string, unknown>
    expect(datos.decision_fecha).toBe('confirmar_documento')
    expect(datos).not.toHaveProperty('fecha_movimiento')
    expect(w.emitted('guardar')).toHaveLength(1)
    expect(w.find('img').attributes('src')).toBe('http://localhost:8000/storage/pagina.webp')
    w.unmount()
  })
  it('envía la fecha solo cuando se elige corregir con evidencia', async () => {
    const w = mount(RevisionHil, { props: { movimiento: m } }); await flushPromises()
    await w.find('select').setValue('corregir')
    await w.find('input[type="date"]').setValue('2026-02-03')
    await w.find('textarea').setValue('Error de lectura contrastado con la fotografía')
    await w.find('form').trigger('submit'); await flushPromises()
    expect(api.put).toHaveBeenCalledWith('/kardex/movimiento/7', expect.objectContaining({ fecha_movimiento: '2026-02-03', decision_fecha: 'corregir' }))
    w.unmount()
  })
})
