import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import PreparacionInventarioView from './PreparacionInventarioView.vue'
const { get, auth } = vi.hoisted(() => ({ get: vi.fn(), auth: { rol: 'Administrador' } }))
vi.mock('@/services/api', () => ({ default: { get } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
const fila = { articulo_id: 1, articulo: 'Libro con apertura', codigo: 'QA-1', apertura: true, origen: 'CONTEO_FISICO',
  saldo_operativo: 20, saldo_documental: 20, motivo_bloqueo: null, sin_ubicacion: 20, en_areas: 0, en_custodia: 0,
  integridad: true, conciliacion_registrada: false, conteo_aprobado: true, referencia_base: 'ACTA-QA',
  fecha_base: '2026-10-20T14:00:00Z', registros_posteriores: 0, fuente_cierre: 'PROPUESTA',
  pendientes: ['UBICACION_PENDIENTE'], acciones: ['Verificar la ubicación física antes de asignarla.'] }
function respuesta() {
  return { generado_en: '2026-10-29T14:00:00Z', gestion: 2026, periodo_abierto: true,
    resumen: { articulos: 3, aperturas: 2, conciliaciones: 0, unidades_sin_ubicacion: 26,
      unidades_sin_ubicacion_con_indicio_prueba: 20, unidades_sin_ubicacion_sin_indicio_prueba: 6,
      articulos_con_unidades_sin_ubicacion: 2, bases_bloqueadas: 0, fuentes_sin_confirmar: 3, pendientes_por_tipo: {} },
    areas_activas: [{ id: 2, nombre: 'Galería' }], transferencias_entre_areas_disponibles: false,
    articulos: [fila, { ...fila, articulo_id: 116, articulo: 'Libro con operaciones', codigo: 'QA-116', origen: 'KARDEX_HISTORICO',
      saldo_operativo: 6, sin_ubicacion: 6, registros_posteriores: 2, conteo_aprobado: false,
      pendientes: ['UBICACION_PENDIENTE','CONTEO_POSTERIOR'], acciones: ['Registrar conteo posterior y ajuste autorizado.'] },
      { ...fila, articulo_id: 3, articulo: 'Libro sin apertura', codigo: 'QA-3', apertura: false,
        saldo_operativo: null, sin_ubicacion: null, en_areas: null, en_custodia: null, pendientes: ['CONTEO_INICIAL'] }],
    alcance: 'Preparación basada en registros; los conteos requieren personal y documentos reales.' }
}
beforeEach(() => { vi.clearAllMocks(); auth.rol = 'Administrador'; get.mockResolvedValue({ data: respuesta() }) })
async function montar() {
  const w = mount(PreparacionInventarioView, { global: { stubs: { RouterLink: RouterLinkStub } } })
  await flushPromises(); return w
}
describe('Preparación del inventario', () => {
  it('prioriza aperturas y distingue saldo documental de operativo', async () => {
    const w = await montar()
    expect(w.text()).toContain('26')
    expect(w.text()).toContain('2 de 3 artículos')
    expect(w.text()).toContain('Conteo posterior y ajuste')
    expect(w.text()).toContain('al menos dos ubicaciones')
    expect(w.text()).toContain('20 pertenecen a registros con indicios de prueba')
    await w.get('input[type="checkbox"]').setValue(false)
    expect(w.text()).toContain('3 de 3 artículos')
    expect(w.get('tbody').text()).toContain('Sin base operativa')
    const links = w.findAllComponents(RouterLinkStub)
    expect(links.some(l => {
      const destino = l.props('to')
      return typeof destino === 'object' && destino?.query?.articulo_id === 116
    })).toBe(true)
    w.unmount()
  })
  it('prepara una ficha con conteos en blanco y no confirma datos al imprimir', async () => {
    const imprimir = vi.spyOn(window, 'print').mockImplementation(() => {})
    const w = await montar()
    await w.findAll('button').find(b => b.text() === 'Preparar ficha')!.trigger('click')
    const ficha = w.get('section[aria-label="Ficha de cotejo"]')
    expect(ficha.text()).toContain('Total físico cotejado: __________')
    expect(ficha.text()).toContain('Persona que cuenta:')
    expect(ficha.text()).toContain('Esta ficha preparada no confirma un conteo')
    expect(ficha.find('input').exists()).toBe(false)
    await ficha.findAll('button').find(b => b.text() === 'Imprimir ficha')!.trigger('click')
    expect(imprimir).toHaveBeenCalledOnce()
    expect(get).toHaveBeenCalledTimes(1)
    w.unmount(); imprimir.mockRestore()
  })
  it.each(['Administrador','Auditor','Operador'])('permite consulta y ficha a %s sin escrituras', async rol => {
    auth.rol = rol
    const w = await montar()
    expect(w.find('table').exists()).toBe(true)
    expect(w.text().includes('Áreas y catálogos')).toBe(rol !== 'Operador')
    expect(w.text()).not.toContain('Guardar conteo')
    w.unmount()
  })
  it('permite recuperar un fallo de consulta', async () => {
    get.mockRejectedValueOnce(new Error('Conexión'))
    const w = await montar()
    expect(w.get('[role="alert"]').text()).toContain('volver a intentar')
    await w.findAll('button').find(b => b.text() === 'Actualizar')!.trigger('click'); await flushPromises()
    expect(w.find('[role="alert"]').exists()).toBe(false)
    expect(w.text()).toContain('Libro con apertura')
    w.unmount()
  })
})
