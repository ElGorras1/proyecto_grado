import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import api from '@/services/api'
import ReporteInventarioView from './ReporteInventarioView.vue'

const { routeQuery } = vi.hoisted(() => ({ routeQuery: {} as Record<string, string> }))
vi.mock('vue-router', () => ({ useRoute: () => ({ query: routeQuery }) }))
vi.mock('@/services/api', () => ({ default: { get: vi.fn() } }))
const obtener = vi.mocked(api.get)

const datos = {
  gestion: 2026,
  resumen: {
    movimientos: 2,
    articulos: 1,
    ingresos: 10,
    salidas: 2,
    pendientes_hil: 1,
    historicos: 1,
    modernos: 1,
  },
  mensual: Array.from({ length: 12 }, (_, i) => ({
    mes: i + 1,
    movimientos: i === 0 ? 2 : 0,
    ingresos: i === 0 ? 10 : 0,
    salidas: i === 0 ? 2 : 0,
  })),
  pagina: 1,
  limite: 50,
  filas: [
    {
      id: 1,
      fecha: '2026-01-02',
      articulo: 'Libro A',
      codigo: 'LIB-001',
      origen: 'Histórico',
      lote_id: 1,
      pagina: 1,
      orden_fila: 2,
      detalle: 'Salida',
      referencia: null,
      area_original: null,
      nodo: 'Área: Biblioteca',
      tipo_operacion: null,
      ingresos: 0,
      salidas: 2,
      pendiente_hil: true,
    },
  ],
}

beforeEach(() => {
  vi.resetAllMocks()
  Object.keys(routeQuery).forEach((k) => delete routeQuery[k])
  obtener.mockImplementation(async (url) => {
    if (url === '/reportes/inventario/opciones') {
      return { data: { gestiones: [2026, 2025], nodos: ['Área: Biblioteca'] } } as never
    }
    return { data: datos } as never
  })
})

describe('Reportes por gestión', () => {
  it('consulta las fechas sin gestión confirmada sin asignarles un año', async () => {
    const w = mount(ReporteInventarioView, { global: { stubs: ['router-link'] } })
    await flushPromises()
    obtener.mockResolvedValue({ data: { ...datos, gestion: null, filas: [{ ...datos.filas[0], fecha: null, fecha_documental_texto: '08/2023', fecha_precision: 'PARCIAL' }] } } as never)
    await w.get('select[aria-label="Gestión"]').setValue('')
    await w.get('form').trigger('submit'); await flushPromises()
    const calls = vi.mocked(api.get).mock.calls
    const params = calls[calls.length - 1]?.[1]?.params
    expect(params).not.toHaveProperty('gestion')
    expect(params).not.toHaveProperty('mes')
    expect(w.text()).toContain('Sin fecha completa')
    expect(w.text()).toContain('08/2023')
    expect(w.find('[aria-label="Distribución mensual"]').exists()).toBe(false)
    w.unmount()
  })
  it('muestra el resumen y envía filtros combinados al backend', async () => {
    const wrapper = mount(ReporteInventarioView, { global: { stubs: ['router-link'] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Pendientes HIL')
    expect(wrapper.text()).toContain('Libro A')
    expect(wrapper.text()).toContain('no representa existencias al cierre de año')
    await wrapper.find('input[type="search"]').setValue('LIB-001')
    const selects = wrapper.findAll('.filtros select')
    await selects[1].setValue('2')
    await selects[2].setValue('historico')
    await selects[5].setValue('pendiente')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(obtener).toHaveBeenLastCalledWith('/reportes/inventario', {
      params: {
        gestion: 2025,
        mes: 2,
        articulo: 'LIB-001',
        origen: 'historico',
        direccion: 'todas',
        revision: 'pendiente',
        pagina: 1,
        limite: 50,
      },
    })
    wrapper.unmount()
  })
})

it('respeta la gestión y origen del enlace institucional aunque existan años más recientes', async () => {
  routeQuery.gestion = '2025'
  routeQuery.origen = 'historico'
  const wrapper = mount(ReporteInventarioView, { global: { stubs: ['router-link'] } })
  await flushPromises()
  expect(obtener).toHaveBeenCalledWith('/reportes/inventario', {
    params: {
      gestion: 2025,
      origen: 'historico',
      direccion: 'todas',
      revision: 'todas',
      pagina: 1,
      limite: 50,
    },
  })
  expect((wrapper.get('form select').element as HTMLSelectElement).value).toBe('2025')
  wrapper.unmount()
})

it('abre el archivo hasta 2025 y permite consultar operaciones digitales posteriores expresamente', async () => {
  obtener.mockImplementation(async (url) => url === '/reportes/inventario/opciones'
    ? { data: { gestiones: [2026, 2025, 2024], gestiones_historicas: [2024], nodos: [] } } as never
    : { data: datos } as never)
  const w = mount(ReporteInventarioView, { global: { stubs: ['router-link'] } })
  await flushPromises()
  expect(obtener).toHaveBeenCalledWith('/reportes/inventario', expect.objectContaining({ params: expect.objectContaining({ gestion: 2024, origen: 'historico' }) }))
  await w.get('[aria-label="Gestión"]').setValue('2026')
  await w.get('[aria-label="Origen"]').setValue('moderno')
  expect(w.text()).toContain('Hay filtros sin aplicar')
  await w.get('form').trigger('submit'); await flushPromises()
  expect(obtener).toHaveBeenLastCalledWith('/reportes/inventario', expect.objectContaining({ params: expect.objectContaining({ gestion: 2026, origen: 'moderno' }) }))
  w.unmount()
})

it('no asigna un año digital al archivo sin fechas históricas completas', async () => {
  obtener.mockImplementation(async (url) => url === '/reportes/inventario/opciones'
    ? { data: { gestiones: [2026], gestiones_historicas: [], nodos: [] } } as never
    : { data: { ...datos, gestion: null } } as never)
  const w = mount(ReporteInventarioView, { global: { stubs: ['router-link'] } })
  await flushPromises()
  const params = obtener.mock.calls.find(c => c[0] === '/reportes/inventario')![1]!.params
  expect(params).toMatchObject({ origen: 'historico' })
  expect(params).not.toHaveProperty('gestion')
  w.unmount()
})
