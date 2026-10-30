import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AreasCatalogosView from './AreasCatalogosView.vue'
const { get, post, put, auth } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), put: vi.fn(), auth: { rol: 'Administrador' } }))
vi.mock('@/services/api', () => ({ default: { get, post, put } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
const base = '/administracion/areas'
beforeEach(() => {
  vi.clearAllMocks(); auth.rol = 'Administrador'
  get.mockImplementation((url: string) => Promise.resolve({ data:
    url === base ? [{ id: 1, version: 'a'.repeat(64), nombre: 'Galería', codigo: 'GAL', estado: 'activo', dependencias: { stock: 3, custodias_abiertas: 0, usuarios_activos: 1 } }] :
    url.endsWith('/historico') ? [{ id: 2, version: 'b'.repeat(64), nombre_oficial: 'C+C', abreviatura: 'C+C', tipo: 'departamento', activa: false }] :
    url.endsWith('/alias') ? [{ id: 3, version: 'c'.repeat(64), texto_sucio: 'CTC', area_oficial_id: 2, confirmado: false, activa: true }] :
    [{ id: 4, version: 'd'.repeat(64), nombre: 'Persona QA', area_id: 1, estado: 'activo' }]
  }))
  post.mockResolvedValue({ data: {} }); put.mockResolvedValue({ data: {} })
})
async function montar() {
  const w = mount(AreasCatalogosView, { global: { stubs: { RouterLink: RouterLinkStub } } })
  await flushPromises(); return w
}
function boton(w: ReturnType<typeof mount>, texto: string) {
  return w.findAll('button').find(b => b.text().includes(texto))!
}
describe('Administración de áreas y catálogos', () => {
  it('separa ubicaciones, áreas antiguas y adscripción de cuentas', async () => {
    const w = await montar()
    expect(w.text()).toContain('Stock: 3')
    expect(w.text()).not.toContain('C+C ·')
    await boton(w, 'Catálogo histórico').trigger('click')
    expect(w.get('tbody').text()).toContain('C+C')
    expect(w.get('tbody').text()).toContain('Histórica / de baja')
    expect(w.text()).toContain('no habilita una ubicación')
    await boton(w, 'Personas y adscripción').trigger('click')
    expect(w.get('tbody').text()).toContain('Persona QA')
    expect(w.get('tbody').text()).toContain('Galería')
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('crea área con motivo y conserva el formulario si el servidor rechaza la baja', async () => {
    const w = await montar()
    await boton(w, 'Nuevo registro').trigger('click')
    const form = w.get('form')
    await form.findAll('input')[0].setValue('Depósito')
    await form.get('textarea[maxlength="2000"]').setValue('Alta aprobada según acta QA 01')
    await form.trigger('submit'); await flushPromises()
    expect(post).toHaveBeenCalledWith(base, expect.objectContaining({ nombre: 'Depósito', estado: 'activo', motivo: 'Alta aprobada según acta QA 01' }))
    await boton(w, 'Editar').trigger('click')
    await w.get('form select').setValue('baja')
    put.mockRejectedValue({ response: { data: { detail: 'Hay stock pendiente en esta área.' } } })
    await w.get('form').trigger('submit'); await flushPromises()
    expect(w.get('[role="alert"]').text()).toContain('Hay stock pendiente')
    expect(w.find('form').exists()).toBe(true)
    expect(put).toHaveBeenCalledWith(base + '/1', expect.objectContaining({ version: 'a'.repeat(64), estado: 'baja' }))
    w.unmount()
  })
  it('requiere cotejo explícito al confirmar un alias y lo envía con su versión', async () => {
    const w = await montar()
    await boton(w, 'Alias y siglas').trigger('click')
    expect(w.text()).toContain('Sugerencia sin confirmar')
    await boton(w, 'Editar').trigger('click')
    expect(w.get<HTMLInputElement>('form input[readonly]').element.value).toBe('CTC')
    const confirmado = w.findAll('input[type="checkbox"]')[0]
    await confirmado.setValue(true)
    expect(w.get('button[type="submit"]').attributes('disabled')).toBeDefined()
    const evidencia = w.findAll<HTMLInputElement>('input[type="checkbox"]')[1]
    expect(evidencia.element.checked).toBe(false)
    await evidencia.setValue(true)
    await w.get('form textarea').setValue('Cotejo en foto y acta del archivo QA 02')
    await w.get('form').trigger('submit'); await flushPromises()
    expect(put).toHaveBeenCalledWith(base + '/catalogo/alias/3', expect.objectContaining({
      confirmado: true, evidencia_revisada: true, texto_sucio: 'CTC', version: 'c'.repeat(64),
    }))
    w.unmount()
  })
  it('permite al auditor consultar sin exponer controles de escritura', async () => {
    auth.rol = 'Auditor'
    const w = await montar()
    expect(w.text()).toContain('Consulta de solo lectura')
    expect(w.text()).not.toContain('Nuevo registro')
    expect(w.text()).not.toContain('Gestionar cuentas y roles')
    for (const nombre of ['Catálogo histórico', 'Alias y siglas', 'Personas y adscripción']) {
      await boton(w, nombre).trigger('click')
      expect(w.find('form').exists()).toBe(false)
      expect(w.get('tbody').text()).not.toContain('Editar')
    }
    expect(post).not.toHaveBeenCalled(); expect(put).not.toHaveBeenCalled()
    w.unmount()
  })
  it('recupera un fallo de carga sin crear registros', async () => {
    get.mockRejectedValueOnce(new Error('conexión'))
    const w = await montar()
    expect(w.get('[role="alert"]').text()).toContain('Actualizar')
    await boton(w, 'Actualizar').trigger('click'); await flushPromises()
    expect(w.find('[role="alert"]').exists()).toBe(false)
    expect(w.text()).toContain('Galería')
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('muestra el motivo, autor y valores del historial sin exponer la versión técnica', async () => {
    const anterior = get.getMockImplementation()!
    get.mockImplementation((url: string) => url.endsWith('/historial') ? Promise.resolve({ data: [{
      id: 1, fecha: '2026-10-29T12:00:00Z', usuario: 'Administración QA',
      detalle: { previo: { estado: 'baja' }, nuevo: { estado: 'activo', version: 'huella-interna' }, motivo: 'Reactivación respaldada en acta QA.' },
    }] }) : anterior(url))
    const w = await montar()
    await boton(w, 'Ver cambios').trigger('click'); await flushPromises()
    const h = w.get('section[aria-label="Historial de cambios"]')
    expect(h.text()).toContain('Administración QA')
    expect(h.text()).toContain('Reactivación respaldada en acta QA.')
    expect(h.text()).toContain('baja → activo')
    expect(h.text()).not.toContain('huella-interna')
    w.unmount()
  })
})
