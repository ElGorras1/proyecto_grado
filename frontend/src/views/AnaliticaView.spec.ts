import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import AnaliticaView from './AnaliticaView.vue'
const { get, post, auth } = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  auth: { rol: 'Administrador' },
}))
vi.mock('@/services/api', () => ({
  default: { get, post, defaults: { baseURL: 'http://localhost:8000/api/v1' } },
}))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
vi.mock('vue-router', () => ({ useRoute: () => ({ query: { gestion: '2021' } }) }))
const perfil = {
  historicos_activos: 200,
  elegibles: 180,
  total: 200,
  exclusiones: { pendientes_hil: 20 },
  por_gestion: { '2021': { disponibles: 200, elegibles: 180 } },
}
let hayModelo = false
const modelo = {
  id: 'modelo-1',
  estado: 'COMPLETADO',
  creado_en: '2026-10-06T12:00:00Z',
  perfil,
  metricas: null,
  umbral: 0.6,
  datos_cambiaron: true,
}
beforeEach(() => {
  vi.useFakeTimers()
  auth.rol = 'Administrador'
  hayModelo = false
  get.mockReset()
  post.mockReset()
  get.mockImplementation((url: string) => {
    if (url.endsWith('/perfil')) return Promise.resolve({ data: perfil })
    if (url.endsWith('/modelos'))
      return Promise.resolve({
        data: { filas: hayModelo ? [modelo] : [], total: hayModelo ? 1 : 0 },
      })
    if (url.endsWith('/evaluacion')) return Promise.resolve({ data: {} })
    if (url.endsWith('/modelos/modelo-1')) return Promise.resolve({ data: modelo })
    return Promise.resolve({ data: { total: 0, filas: [] } })
  })
})
afterEach(() => {
  vi.useRealTimers()
})
function montar() {
  return mount(AnaliticaView, { global: { stubs: { RouterLink: RouterLinkStub, ReglasHistoricas: true } } })
}
describe('Auditoría histórica', () => {
  it('conserva una búsqueda escrita mientras termina la consulta anterior', async () => {
    hayModelo = true
    const w = montar()
    await flushPromises()
    const original = get.getMockImplementation()!
    let resolver!: (v: unknown) => void
    get.mockImplementation((url: string, opciones: any) =>
      url === '/analitica/resultados' && opciones.params.articulo === 'Primero'
        ? new Promise((resolve) => {
            resolver = resolve
          })
        : original(url),
    )
    await w.get('input[aria-label="Artículo o código"]').setValue('  Primero  ')
    await w.get('form.filtros').trigger('submit')
    await w.get('input[aria-label="Artículo o código"]').setValue('Segundo')
    resolver({ data: { filas: [], total: 0 } })
    await flushPromises()
    expect((w.get('input[aria-label="Artículo o código"]').element as HTMLInputElement).value).toBe(
      'Segundo',
    )
    expect(w.text()).toContain('Hay cambios sin aplicar')
    await w.get('form.filtros').trigger('submit')
    await flushPromises()
    expect(get).toHaveBeenCalledWith(
      '/analitica/resultados',
      expect.objectContaining({
        params: expect.objectContaining({ articulo: 'Segundo' }),
      }),
    )
    w.unmount()
  })
  it('limpia espacios de búsqueda y permite volver a todos los resultados', async () => {
    hayModelo = true
    const w = montar()
    await flushPromises()
    await w.get('input[aria-label="Artículo o código"]').setValue('  Libro  ')
    await w.get('input[aria-label="Nodo exacto"]').setValue('  Biblioteca  ')
    expect(w.text()).toContain('Hay cambios sin aplicar')
    await w.get('form.filtros').trigger('submit')
    await flushPromises()
    expect(get).toHaveBeenCalledWith(
      '/analitica/resultados',
      expect.objectContaining({
        params: expect.objectContaining({ articulo: 'Libro', nodo: 'Biblioteca', gestion: '2021' }),
      }),
    )
    expect(w.text()).not.toContain('Hay cambios sin aplicar')
    await w
      .findAll('button')
      .find((b) => b.text() === 'Limpiar filtros')!
      .trigger('click')
    await flushPromises()
    expect(get).toHaveBeenCalledWith(
      '/analitica/resultados',
      expect.objectContaining({
        params: expect.objectContaining({
          articulo: undefined,
          nodo: undefined,
          gestion: undefined,
          seleccion: 'todos',
        }),
      }),
    )
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('no informa ausencia de resultados si falla la consulta', async () => {
    hayModelo = true
    const w = montar()
    await flushPromises()
    const original = get.getMockImplementation()!
    get.mockImplementation((url: string) =>
      url === '/analitica/resultados' ? Promise.reject(new Error('sin red')) : original(url),
    )
    await w.get('form.filtros').trigger('submit')
    await flushPromises()
    expect(w.text()).toContain('No se pudo completar la consulta')
    expect(w.text()).not.toContain('No hay resultados para estos filtros')
    w.unmount()
  })
  it('muestra preparación y estado sin modelos, y permite entrenar al administrador', async () => {
    const w = montar()
    await flushPromises()
    expect(w.text()).toContain('Todavía no hay modelos')
    expect(w.text()).toContain('180')
    expect(w.text()).toContain('Entrenar nueva versión')
    w.unmount()
  })
  it.each(['Operador', 'Auditor'])('no ofrece entrenamiento al %s', async (rol) => {
    auth.rol = rol
    const w = montar()
    await flushPromises()
    expect(w.text()).not.toContain('Entrenar nueva versión')
    w.unmount()
  })
  it('conserva gestión desde reportes y avisa de cambios posteriores al corte', async () => {
    hayModelo = true
    const w = montar()
    await flushPromises()
    expect(get).toHaveBeenCalledWith(
      '/analitica/resultados',
      expect.objectContaining({ params: expect.objectContaining({ gestion: '2021' }) }),
    )
    expect(w.text()).toContain('Hay cambios posteriores al corte')
    expect(w.text()).toContain('No hay resultados para estos filtros')
    w.unmount()
  })
  it('comunica un fallo sin mostrar éxito', async () => {
    get.mockRejectedValue(new Error('sin conexión'))
    const w = montar()
    await flushPromises()
    expect(w.get('[role="alert"]').text()).toContain('No se pudo completar')
    w.unmount()
  })
})

it('ignora detalles tardíos después de aplicar filtros', async () => {
  hayModelo = true
  const original = get.getMockImplementation()!
  const fila = {
    id: 1,
    movimiento_id: 1,
    score: 0.7,
    alerta: true,
    particion: 'evaluacion',
    estado_revision: 'PENDIENTE',
    revision_numero: 0,
    snapshot: { id: 1, articulo: 'Ejemplo', fecha: '2021-01-01', ingresos: 0, salidas: 5 },
    contexto: { mediana: 1, referencias: 20, indicadores: [] },
    vecinos: [],
    revisiones: [],
  }
  let resolver!: (value: unknown) => void
  get.mockImplementation((url: string) => {
    if (url.endsWith('/resultados/1'))
      return new Promise((resolve) => {
        resolver = resolve
      })
    if (url.endsWith('/resultados')) return Promise.resolve({ data: { total: 1, filas: [fila] } })
    return original(url)
  })
  const w = montar()
  await flushPromises()
  await w
    .findAll('button')
    .find((b) => b.text() === 'Ver evidencia')!
    .trigger('click')
  await w.get('form.filtros').trigger('submit')
  await flushPromises()
  resolver({ data: fila })
  await flushPromises()
  expect(w.find('[aria-label="Evidencia del hallazgo"]').exists()).toBe(false)
  w.unmount()
})

it('mantiene los filtros aplicados al paginar y usa los nuevos solo al confirmar', async () => {
  hayModelo = true
  const original = get.getMockImplementation()!
  get.mockImplementation((url: string) =>
    url.endsWith('/resultados')
      ? Promise.resolve({ data: { total: 60, filas: [] } })
      : original(url),
  )
  const w = montar()
  await flushPromises()
  await w.get('form.filtros input').setValue('Artículo nuevo')
  await w
    .findAll('button')
    .find((b) => b.text() === 'Siguiente')!
    .trigger('click')
  await flushPromises()
  expect(get).toHaveBeenLastCalledWith('/analitica/modelos/modelo-1/diagnostico')
  const consultas = () => get.mock.calls.filter((c) => c[0] === '/analitica/resultados')
  expect(consultas()[consultas().length - 1]?.[1].params).toMatchObject({
    pagina: 2,
    articulo: undefined,
  })
  await w.get('form.filtros').trigger('submit')
  await flushPromises()
  expect(consultas()[consultas().length - 1]?.[1].params).toMatchObject({
    pagina: 1,
    articulo: 'Artículo nuevo',
  })
  w.unmount()
})

it('abre la selección de revisión completa aunque se haya entrado desde una gestión', async () => {
  hayModelo = true
  const original = get.getMockImplementation()!
  const v = {
    k: 20,
    disponibles: 20,
    revisados_concluyentes: 0,
    relevantes: 0,
    pendientes: 20,
    errores_documentales: 0,
    no_concluyentes: 0,
    sin_resultado: 0,
    ids_duplicados: 0,
    seleccion_integra: true,
    precision_at_k: null,
  }
  get.mockImplementation((url: string) => {
    if (url.endsWith('/modelos/modelo-1'))
      return Promise.resolve({
        data: {
          ...modelo,
          metricas: {
            particiones: { entrenamiento: 120, calibracion: 40, evaluacion: 40 },
            alertas: 8,
            k: 20,
            jaccard_top_entre_semillas: [1, 1],
            solapamiento_top_regla: 0.15,
            sin_referencia_propia_evaluacion: 28,
            evaluacion_humana: 'Pendiente',
          },
        },
      })
    if (url.endsWith('/diagnostico'))
      return Promise.resolve({
        data: {
          version: 1,
          modelo_id: 'modelo-1',
          estado: 'CONSISTENTE',
          comprobaciones: [],
          reproduccion_artefacto: 'NO_VERIFICADO',
          cobertura: {
            evaluados: 200,
            evaluacion: 40,
            sin_referencia_propia: 28,
            porcentaje_sin_referencia: 70,
          },
          evaluacion: { modelo: v, regla: v, control: v, advertencia: 'Pendiente' },
        },
      })
    return original(url)
  })
  const w = montar()
  await flushPromises()
  expect(w.text()).toContain('Comprobación técnica')
  await w
    .findAll('button')
    .find((b) => b.text() === 'Revisar selección')!
    .trigger('click')
  await flushPromises()
  const consultas = get.mock.calls.filter((c) => c[0] === '/analitica/resultados')
  expect(consultas[consultas.length - 1]?.[1].params).toMatchObject({
    pagina: 1,
    seleccion: 'top_modelo',
    gestion: undefined,
    articulo: undefined,
    estado: undefined,
  })
  w.unmount()
})
