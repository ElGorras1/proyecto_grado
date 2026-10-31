import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import AnaliticaView from './AnaliticaView.vue'
const { get, post, auth, ruta } = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  auth: { rol: 'Administrador' },
  ruta: { gestion: '2021' } as Record<string, string | undefined>,
}))
vi.mock('@/services/api', () => ({
  default: { get, post, defaults: { baseURL: 'http://localhost:8000/api/v1' } },
}))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
vi.mock('vue-router', () => ({ useRoute: () => ({ query: ruta }) }))
const perfil = {
  historicos_activos: 200,
  elegibles: 180,
  total: 200,
  exclusiones: { pendientes_hil: 20 },
  por_gestion: { '2021': { disponibles: 200, elegibles: 180 } },
  por_articulo: {
    '1': { nombre: 'Historia institucional', disponibles: 190, elegibles: 180 },
    '2': { nombre: 'Historia institucional suplemento', disponibles: 10, elegibles: 0 },
  },
}
const resumen = { modelo_id: 'modelo-1', totales: { analizados: 180, alertas: 8, no_elegibles: 20 },
  alcance: 'Puntajes del corte por fecha documental; no son anomalías confirmadas.',
  gestiones: [{ gestion: '2021', documentales: 200, elegibles: 180, analizados: 180, alertas: 8,
    no_elegibles: 20, elegibles_sin_puntuar: 0, evaluacion_reservada: 36, estado: 'PUNTUACION_COMPLETA' }] }
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
  ruta.gestion = '2021'
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
    if (url.endsWith('/gestiones')) return Promise.resolve({ data: resumen })
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
  it('enlaza HIL y grafo conservando la identidad del artículo del hallazgo', async () => {
    hayModelo = true
    const original = get.getMockImplementation()!
    const fila = { id: 8, articulo_id: 7, movimiento_id: 99, score: 0.7, alerta: true,
      particion: 'evaluacion', estado_revision: 'PENDIENTE', revision_numero: 0,
      snapshot: { articulo: 'Artículo del corte', fecha: '2021-01-01' },
      contexto: { mediana: 1, referencias: 10, indicadores: [] }, vecinos: [], revisiones: [] }
    get.mockImplementation((url: string) => url.endsWith('/resultados/8')
      ? Promise.resolve({ data: fila }) : url.endsWith('/resultados')
        ? Promise.resolve({ data: { total: 1, filas: [fila] } }) : original(url))
    const w = montar()
    await flushPromises()
    await w.findAll('button').find(b => b.text() === 'Ver evidencia')!.trigger('click'); await flushPromises()
    const enlaces = w.findAllComponents(RouterLinkStub).filter(l => l.text().includes('este artículo'))
    expect(enlaces.map(l => l.props('to'))).toEqual([
      { path: '/kardex-digital', query: { articulo_id: 7, tab: 'hil' } },
      { path: '/kardex-digital', query: { articulo_id: 7, tab: 'grafo' } },
    ])
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('descarga todos los resultados de la consulta aplicada y bloquea filtros sin aplicar', async () => {
    hayModelo = true
    const original = get.getMockImplementation()!
    get.mockImplementation((url: string) => url.endsWith('.csv')
      ? Promise.resolve({ data: new Blob(['Modelo;Movimiento ID\nmodelo-1;8']) }) : original(url))
    const createUrl = vi.fn(() => 'blob:auditoria')
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: createUrl })
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() })
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    const w = montar()
    try {
      await flushPromises()
      const descargar = () => w.findAll('button').find(b => b.text() === 'Descargar auditoría filtrada CSV')!
      await w.get('[aria-label="Artículo del corte"]').setValue('1')
      expect(descargar().attributes('disabled')).toBeDefined()
      await w.get('form.filtros').trigger('submit'); await flushPromises()
      await descargar().trigger('click'); await flushPromises()
      expect(get).toHaveBeenCalledWith('/analitica/resultados.csv', {
        params: { modelo_id: 'modelo-1', gestion: '2021', articulo: undefined, articulo_id: '1',
          nodo: undefined, estado: undefined, seleccion: 'todos' }, responseType: 'blob',
      })
      expect(click).toHaveBeenCalledTimes(1)
      expect(createUrl).toHaveBeenCalledTimes(1)
      expect(post).not.toHaveBeenCalled()
    } finally { w.unmount(); click.mockRestore() }
  })

  it('muestra un mensaje y permite reintentar si la descarga falla', async () => {
    hayModelo = true
    const original = get.getMockImplementation()!
    get.mockImplementation((url: string) => url.endsWith('.csv') ? Promise.reject(new Error('sin conexión')) : original(url))
    const w = montar()
    await flushPromises()
    await w.findAll('button').find(b => b.text() === 'Descargar auditoría filtrada CSV')!.trigger('click')
    await flushPromises()
    expect(w.text()).toContain('No se pudo descargar la auditoría')
    expect(w.findAll('button').find(b => b.text() === 'Descargar auditoría filtrada CSV')!.attributes('disabled')).toBeUndefined()
    w.unmount()
  })
  it('conserva la consulta anterior mientras se actualiza el servicio del resumen', async () => {
    hayModelo = true
    const original = get.getMockImplementation()!
    get.mockImplementation((url: string) => url.endsWith('/gestiones')
      ? Promise.reject({ isAxiosError: true, response: { status: 404 } }) : original(url))
    const w = montar()
    await flushPromises()
    expect(w.text()).toContain('Resultados por gestión')
    expect(w.find('[role="alert"]').exists()).toBe(false)
    expect(w.find('[aria-label="Artículo del corte"]').exists()).toBe(false)
    w.unmount()
  })
  it('expone cobertura por gestión sin presentar excluidos como normales', async () => {
    hayModelo = true
    const w = montar()
    await flushPromises()
    const tabla = w.get('[aria-label="Cobertura de Isolation Forest por gestión"]')
    expect(tabla.text()).toContain('180 movimientos puntuados')
    expect(tabla.text()).toContain('20 registros no elegibles')
    expect(tabla.text()).toContain('Elegibles puntuados')
    await tabla.get('button').trigger('click')
    await flushPromises()
    expect(get).toHaveBeenCalledWith('/analitica/resultados', expect.objectContaining({ params: expect.objectContaining({ gestion: '2021', pagina: 1 }) }))
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('elige la última gestión del modelo aunque el calendario del equipo sea posterior', async () => {
    hayModelo = true
    delete ruta.gestion
    vi.setSystemTime(new Date('2040-01-01T12:00:00Z'))
    const original = get.getMockImplementation()!
    const corte = { ...perfil, por_gestion: { '2024': { disponibles: 100, elegibles: 90 }, '2025': { disponibles: 100, elegibles: 90 } } }
    const version = { ...modelo, perfil: corte }
    get.mockImplementation((url: string) => {
      if (url.endsWith('/modelos')) return Promise.resolve({ data: { total: 1, filas: [version] } })
      if (url.endsWith('/modelos/modelo-1')) return Promise.resolve({ data: version })
      return original(url)
    })
    const w = montar()
    await flushPromises()
    expect(w.get<HTMLSelectElement>('[aria-label="Gestión documental"]').element.value).toBe('2025')
    expect(get).toHaveBeenCalledWith('/analitica/resultados', expect.objectContaining({ params: expect.objectContaining({ gestion: '2025' }) }))
    w.unmount()
  })
  it('selecciona un artículo exacto y explica la ausencia de elegibles', async () => {
    hayModelo = true
    const w = montar()
    await flushPromises()
    await w.get('[aria-label="Artículo del corte"]').setValue('2')
    expect(w.get('[aria-label="Artículo o código"]').attributes('disabled')).toBeDefined()
    expect(w.text()).toContain('no tiene movimientos elegibles')
    await w.get('form.filtros').trigger('submit')
    await flushPromises()
    expect(get).toHaveBeenCalledWith('/analitica/resultados', expect.objectContaining({ params: expect.objectContaining({ articulo_id: '2', articulo: undefined }) }))
    w.unmount()
  })
  it('conserva una búsqueda escrita mientras termina la consulta anterior', async () => {
    hayModelo = true
    const w = montar()
    await flushPromises()
    const original = get.getMockImplementation()!
    let resolver!: (v: unknown) => void
    get.mockImplementation((url: string, opciones: { params: Record<string, string | number> }) =>
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
