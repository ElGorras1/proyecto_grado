import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AlertasInventarioView from './AlertasInventarioView.vue'
const { get, post, auth } = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  auth: { rol: 'Administrador', usuario: { id: 1 } },
}))
vi.mock('@/services/api', () => ({ default: { get, post } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
vi.mock('vue-router', () => ({ useRoute: () => ({ query: {} }) }))
let caso: any
let vacio = false
beforeEach(() => {
  auth.rol = 'Administrador'
  vacio = false
  caso = {
    id: 3,
    articulo_id: 1,
    articulo: 'Libro de ensayo',
    codigo: 'QA-1',
    estado: 'PENDIENTE',
    prioridad: 'ALTA',
    asignado_id: null,
    asignado_nombre: null,
    revision_numero: 0,
    creado_en: '2026-10-08T14:00:00Z',
    conclusion: null,
    operacion: {
      clase: 'MOVIMIENTO',
      id: 21,
      tipo: 'Ventas',
      cantidad: 6,
      direccion: 'SALIDA',
      documento: 'FACT-01',
      receptor: 'Biblioteca',
      ocurrido_en: '2026-10-08T14:00:00Z',
      registrado_en: '2026-10-08T14:00:00Z',
      justificacion_operador: 'Entrega completa autorizada',
      encargado_id: 1,
      registrador_id: 1,
      area_origen_id: 2,
      area_destino_id: null,
      alertas: [
        {
          codigo: 'AGOTA_AREA',
          nivel: 'alto',
          mensaje: 'La salida utiliza todas las unidades de Galería.',
          datos: { saldo_ubicacion: 6 },
        },
      ],
    },
    actual: { cantidad_vigente: 6 },
    huella_contexto: 'a'.repeat(64),
    personas: { 1: 'Encargada' },
    areas: { 2: 'Galería' },
    historial: { total: 0, filas: [] },
  }
  get.mockReset()
  post.mockReset()
  get.mockImplementation((url: string) =>
    Promise.resolve({
      data:
        url === '/kardex/articulos'
          ? [{ id: 1, nombre: 'Libro de ensayo' }]
          : url === '/control-alertas/revisores'
            ? [
                { id: 1, nombre: 'Encargada', rol: 'Administrador' },
                { id: 2, nombre: 'Auditor', rol: 'Auditor' },
              ]
            : url === '/control-alertas'
              ? {
                  total: vacio ? 0 : 1,
                  filas: vacio ? [] : [{ ...caso }],
                  conteos: vacio ? {} : { [caso.estado]: 1 },
                }
              : { ...caso },
    }),
  )
})
async function montar(abierto = true) {
  const w = mount(AlertasInventarioView, { global: { stubs: { RouterLink: RouterLinkStub } } })
  await flushPromises()
  if (abierto) {
    await w.get('.caso').trigger('click')
    await flushPromises()
  }
  return w
}
describe('Bandeja de alertas operativas', () => {
  it('descarta un historial tardío después de cerrar el caso por filtros', async () => {
    caso.historial = { total: 100, filas: [] }
    const w = await montar()
    const original = get.getMockImplementation()!
    let resolver!: (v: unknown) => void
    get.mockImplementation((url: string) =>
      url.endsWith('/revisiones')
        ? new Promise((resolve) => {
            resolver = resolve
          })
        : original(url),
    )
    await w
      .findAll('button')
      .find((b) => b.text() === 'Más antiguas')!
      .trigger('click')
    await w.get('form[aria-label="Filtrar alertas"]').trigger('submit')
    await flushPromises()
    resolver({ data: { total: 100, filas: [] } })
    await flushPromises()
    expect(w.find('[aria-label="Detalle de alerta"]').exists()).toBe(false)
    expect(w.text()).not.toContain('No se pudo cargar el historial')
    w.unmount()
  })
  it('cierra el detalle al aplicar filtros y descarta una evidencia tardía', async () => {
    const w = await montar()
    expect(w.find('[aria-label="Detalle de alerta"]').exists()).toBe(true)
    let resolver!: (v: unknown) => void
    const original = get.getMockImplementation()!
    get.mockImplementation((url: string) =>
      url === '/control-alertas/3'
        ? new Promise((resolve) => {
            resolver = resolve
          })
        : original(url),
    )
    await w.get('.caso').trigger('click')
    vacio = true
    await w.get('input[aria-label="Gestión de registro"]').setValue('2025')
    expect(w.text()).toContain('Hay cambios sin aplicar')
    await w.get('form[aria-label="Filtrar alertas"]').trigger('submit')
    await flushPromises()
    resolver({ data: caso })
    await flushPromises()
    expect(w.find('[aria-label="Detalle de alerta"]').exists()).toBe(false)
    expect(w.text()).toContain('No hay casos para estos filtros')
    expect(get).toHaveBeenLastCalledWith(
      '/control-alertas',
      expect.objectContaining({
        params: expect.objectContaining({ gestion: 2025, pagina: 1 }),
      }),
    )
    await w
      .findAll('button')
      .find((b) => b.text() === 'Limpiar filtros')!
      .trigger('click')
    await flushPromises()
    expect(get).toHaveBeenLastCalledWith(
      '/control-alertas',
      expect.objectContaining({
        params: expect.objectContaining({
          gestion: undefined,
          articulo_id: undefined,
          estado: 'ABIERTOS',
        }),
      }),
    )
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('no confunde un fallo de red con ausencia de alertas', async () => {
    const w = await montar(false)
    const original = get.getMockImplementation()!
    get.mockImplementation((url: string) =>
      url === '/control-alertas' ? Promise.reject(new Error('sin red')) : original(url),
    )
    await w.get('form').trigger('submit')
    await flushPromises()
    expect(w.text()).toContain('No se pudo cargar la bandeja')
    expect(w.text()).not.toContain('No hay casos para estos filtros')
    expect(w.find('.caso').exists()).toBe(false)
    w.unmount()
  })
  it('distingue la justificación de origen de una revisión pendiente y muestra la evidencia', async () => {
    const w = await montar()
    expect(w.text()).toContain('Entrega completa autorizada')
    expect(w.text()).toContain('Aún no hay decisiones de revisión')
    expect(w.text()).toContain('La salida utiliza todas las unidades de Galería.')
    const siguiente = w.get('select[aria-label="Estado siguiente"]')
    expect(siguiente.findAll('option').map((o) => o.attributes('value'))).toEqual(['EN_REVISION'])
    w.unmount()
  })
  it('permite consultar al operador sin ofrecer decisiones', async () => {
    auth.rol = 'Operador'
    const w = await montar()
    expect(w.find('form[aria-label="Revisar caso"]').exists()).toBe(false)
    expect(w.text()).toContain('FACT-01')
    expect(w.text()).toContain('Solo administradores y auditores')
    w.unmount()
  })
  it('asigna el caso y guarda una revisión con la versión y evidencia vistas', async () => {
    const w = await montar()
    await w.get('select[aria-label="Asignar a"]').setValue(2)
    await w.get('textarea').setValue('Revisión del acta y comprobación con el área')
    post.mockImplementationOnce((_url: string, p: any) => {
      caso = {
        ...caso,
        estado: 'EN_REVISION',
        asignado_id: 2,
        asignado_nombre: 'Auditor',
        revision_numero: 1,
        historial: {
          total: 1,
          filas: [
            {
              id: 1,
              usuario_nombre: 'Encargada',
              creado_en: caso.creado_en,
              anterior: { estado: 'PENDIENTE', prioridad: 'ALTA' },
              nuevo: {
                estado: 'EN_REVISION',
                prioridad: 'ALTA',
                asignado_nombre: 'Auditor',
                conclusion: 'NO_CONCLUYENTE',
              },
              motivo: p.motivo,
              documento: null,
              correccion_movimiento_id: null,
            },
          ],
        },
      }
      return Promise.resolve({ data: caso })
    })
    await w.get('form[aria-label="Revisar caso"]').trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith(
      '/control-alertas/3/revision',
      expect.objectContaining({
        revision_esperada: 0,
        huella_contexto: 'a'.repeat(64),
        estado: 'EN_REVISION',
        asignado_id: 2,
        motivo: 'Revisión del acta y comprobación con el área',
      }),
    )
    expect(w.text()).toContain('Decisión registrada')
    expect(w.text()).toContain('Pendiente → En revisión')
    await w.get('select[aria-label="Estado siguiente"]').setValue('CERRADO')
    await w.get('textarea').setValue('Revisión que aún no presenta una conclusión')
    await w.get('form[aria-label="Revisar caso"]').trigger('submit')
    expect(post).toHaveBeenCalledTimes(1)
    expect(w.text()).toContain('conclusión válida')
    w.unmount()
  })
  it('protege una revisión simultánea y conserva la anotación al actualizar', async () => {
    const w = await montar()
    await w.get('textarea').setValue('Mi anotación sobre el documento revisado')
    post.mockRejectedValueOnce({
      response: { status: 409, data: { detail: 'Otra persona revisó el caso' } },
    })
    await w.get('form[aria-label="Revisar caso"]').trigger('submit')
    await flushPromises()
    expect(w.text()).toContain('Otra persona revisó el caso')
    expect(w.find('button[type="submit"]:disabled').exists()).toBe(true)
    await w.get('form[aria-label="Revisar caso"]').trigger('submit')
    expect(post).toHaveBeenCalledTimes(1)
    caso = { ...caso, estado: 'SEGUIMIENTO', revision_numero: 2 }
    await w
      .findAll('button')
      .find((b) => b.text() === 'Actualizar detalle')!
      .trigger('click')
    await flushPromises()
    expect((w.get('textarea').element as HTMLTextAreaElement).value).toBe(
      'Mi anotación sobre el documento revisado',
    )
    post.mockResolvedValueOnce({ data: { ...caso, revision_numero: 3, estado: 'EN_REVISION' } })
    await w.get('form[aria-label="Revisar caso"]').trigger('submit')
    await flushPromises()
    expect(post.mock.calls[1][1].revision_esperada).toBe(2)
    w.unmount()
  })
  it('conserva la misma clave cuando la respuesta es incierta', async () => {
    const w = await montar()
    await w.get('textarea').setValue('Motivo documentado para iniciar la revisión')
    post
      .mockRejectedValueOnce(new Error('Sin conexión'))
      .mockResolvedValueOnce({ data: { ...caso, estado: 'EN_REVISION', revision_numero: 1 } })
    await w.get('form[aria-label="Revisar caso"]').trigger('submit')
    await flushPromises()
    await w.get('form[aria-label="Revisar caso"]').trigger('submit')
    await flushPromises()
    expect(post.mock.calls[0][1]).toEqual(post.mock.calls[1][1])
    w.unmount()
  })
  it('filtra sin modificar casos y explica la bandeja vacía', async () => {
    vacio = true
    const w = await montar(false)
    expect(w.text()).toContain('No hay casos para estos filtros')
    await w.get('select[aria-label="Revisor asignado"]').setValue('sin')
    await w.get('input[aria-label="Desde"]').setValue('2026-10-08')
    await w.get('form[aria-label="Filtrar alertas"]').trigger('submit')
    await flushPromises()
    expect(get).toHaveBeenLastCalledWith(
      '/control-alertas',
      expect.objectContaining({
        params: expect.objectContaining({ sin_asignar: true, desde: '2026-10-08' }),
      }),
    )
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
})
