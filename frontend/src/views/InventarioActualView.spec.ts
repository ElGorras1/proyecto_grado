import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import InventarioActualView from './InventarioActualView.vue'
const { get, post, auth } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), auth: { rol: 'Administrador', usuario: { id: 1 } } }))
vi.mock('@/services/api', () => ({ default: { get, post } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
vi.mock('vue-router', () => ({ useRoute: () => ({ query: {} }) }))
let articulo: { id: number; codigo: string; nombre: string; stock_actual: number | null;
  apertura: Record<string, unknown> | null; base_kardex?: Record<string, unknown> }
beforeEach(() => {
  auth.rol = 'Administrador'
  articulo = { id: 1, codigo: 'QA-1', nombre: 'Libro', stock_actual: null, apertura: null }
  get.mockReset(); post.mockReset()
  get.mockImplementation((url: string) => Promise.resolve({ data:
    url === '/kardex/articulos' ? [{...articulo}] :
    url === '/kardex/nodos' ? [{ valor: 'Ventas', etiqueta: 'Ventas', grupo: 'Tipo de Operación' }] :
    url === '/kardex/operaciones-inventario' ? [{ valor: 'Ventas', direccion: 'salida', requiere_receptor: true, habilitada: true }] :
    url.includes('/conciliacion-inicial') ? { estado: 'NO_DISPONIBLE', motivo: 'Sin conteo inicial' } :
    url.includes('/existencias-area') ? { total_institucional: articulo.stock_actual, sin_ubicacion_confirmada: articulo.stock_actual, areas: [], estado: 'SIN_APERTURA' } :
    url === '/kardex/encargados' ? [{ id: 1, nombre: 'Encargada' }] : [] }))
})

describe('Control inmediato de movimientos', () => {
  it('vincula la recepción parcial con la entrega original', async () => {
    articulo.stock_actual = 8
    articulo.apertura = { cantidad_inicial: 10, cantidad_actual: 8,
      aprobado_en: '2026-10-06T20:00:00Z', referencia_documento: 'ACTA-01',
      ultimo_moderno_id: 0, origen: 'CONTEO_FISICO' }
    get.mockImplementation((url: string) => Promise.resolve({ data:
      url === '/kardex/articulos' ? [{ ...articulo }] :
      url === '/kardex/operaciones-inventario' ? [
        { valor: 'Devolución', direccion: 'ingreso', requiere_receptor: false, habilitada: true }
      ] :
      url === '/kardex/devoluciones-disponibles/1' ? [
        { id: 23, tipo_operacion: 'Ventas', receptor: 'Biblioteca',
          cantidad_original: 4, cantidad_devuelta: 2, cantidad_pendiente: 2,
          referencia_documento: 'FACT-01', ocurrido_en: '2026-10-07T15:00:00Z' }
      ] :
      url === '/kardex/areas-operativas' ? [{ id: 2, nombre: 'Galería' }] :
      url === '/kardex/encargados' ? [{ id: 1, nombre: 'Encargada' }] :
      url.includes('/existencias-area') ? { total_institucional: 8,
        sin_ubicacion_confirmada: 8, areas: [], estado: 'DISTRIBUCION_PARCIAL' } : [] }))
    const w = await detalle()
    await w.get('button.btn-primary.mt-4').trigger('click')
    await flushPromises()
    await w.findAll('select')[0].setValue('Devolución')
    await w.get('#devolucion-origen').setValue('23')
    await w.get('#devolucion-persona').setValue('Biblioteca')
    await w.get('#movimiento-area-operativa').setValue('2')
    await w.get('#movimiento-referencia').setValue('ACTA-DEV-01')
    await w.get('input[type="number"]').setValue(2)
    post.mockResolvedValue({ data: { saldo_registrado: 10 } })
    await w.get('.actions button').trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/kardex/movimiento-actual',
      expect.objectContaining({ tipo: 'ingreso', tipo_operacion: 'Devolución',
        movimiento_origen_id: 23, devuelto_por: 'Biblioteca',
        area_operativa_id: 2, cantidad: 2, referencia_documento: 'ACTA-DEV-01' }))
    w.unmount()
  })
  it('envía segundos actuales al iniciar la primera operación desde la base histórica', async () => {
    articulo.stock_actual = 18
    articulo.base_kardex = { saldo: 18, movimiento_id: 27, lote_id: 4,
      fecha_movimiento: '2025-12-31', operable: true, motivo_bloqueo: null }
    const w = await detalle()
    await w.get('button.btn-primary.mt-4').trigger('click')
    await w.findAll('select')[0].setValue('Ventas')
    await w.get('#receptor-operacion').setValue('Biblioteca')
    await w.get('#tipo-receptor-operacion').setValue('INSTITUCION')
    await w.get('#movimiento-referencia').setValue('FACT-01')
    post.mockResolvedValue({ data: { saldo_registrado: 17 } })
    const antes = Date.now()
    await w.get('.actions button').trigger('click')
    await flushPromises()
    const fecha = post.mock.calls[0][1].fecha_operacion
    expect(Math.abs(Date.parse(fecha) - antes)).toBeLessThan(5000)
    w.unmount()
  })
  it('exige documento y envía la hora ocurrida separada del registro', async () => {
    articulo.stock_actual = 10
    articulo.apertura = { cantidad_inicial: 10, aprobado_en: '2026-10-06T20:00:00Z',
      referencia_documento: 'ACTA-01', ultimo_moderno_id: 0 }
    const w = await detalle()
    await w.get('button.btn-primary.mt-4').trigger('click')
    await w.findAll('select')[0].setValue('Ventas')
    await w.get('#receptor-operacion').setValue('Biblioteca')
    await w.get('#tipo-receptor-operacion').setValue('INSTITUCION')
    await w.get('#movimiento-fecha-operacion').setValue('2026-10-08T10:30')
    await w.get('.actions button').trigger('click')
    expect(post).not.toHaveBeenCalled()
    expect(w.text()).toContain('documento de respaldo')
    await w.get('#movimiento-referencia').setValue('ACTA-VENTA-01')
    post.mockResolvedValue({ data: { saldo_registrado: 9 } })
    await w.get('.actions button').trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/kardex/movimiento-actual',
      expect.objectContaining({ fecha_operacion: '2026-10-08T14:30:00.000Z',
        referencia_documento: 'ACTA-VENTA-01', area_operativa_id: null,
        encargado_id: 1 }))
    w.unmount()
  })
  it('fija ingreso para compra y evita una dirección contraria en la interfaz', async () => {
    articulo.stock_actual = 10
    articulo.apertura = { cantidad_inicial: 10, aprobado_en: '2026-10-06T20:00:00Z',
      referencia_documento: 'ACTA-01', ultimo_moderno_id: 0 }
    get.mockImplementation((url: string) => Promise.resolve({ data:
      url === '/kardex/articulos' ? [{ ...articulo }] :
      url === '/kardex/nodos' ? [{ valor: 'Inventario / Compra', etiqueta: 'Compra', grupo: 'Tipo de Operación' }] :
      url === '/kardex/operaciones-inventario' ? [{ valor: 'Inventario / Compra', direccion: 'ingreso', requiere_receptor: false, habilitada: true }] :
      url.includes('/conciliacion-inicial') ? { estado: 'NO_DISPONIBLE', motivo: 'Sin conteo inicial' } :
      url.includes('/existencias-area') ? { total_institucional: articulo.stock_actual, sin_ubicacion_confirmada: articulo.stock_actual, areas: [], estado: 'SIN_APERTURA' } :
      url === '/kardex/encargados' ? [{ id: 1, nombre: 'Encargada' }] : [] }))
    const w = await detalle()
    await w.get('button.btn-primary.mt-4').trigger('click')
    await w.findAll('select')[0].setValue('Inventario / Compra')
    await flushPromises()
    const direccion = w.findAll('select')[1]
    expect((direccion.element as HTMLSelectElement).value).toBe('ingreso')
    expect(direccion.attributes('disabled')).toBeDefined()
    w.unmount()
  })
  it('muestra avisos antes de confirmar y exige justificación', async () => {
    articulo.stock_actual = 10
    articulo.apertura = { cantidad_inicial: 10, aprobado_en: '2026-10-06T20:00:00Z',
      referencia_documento: 'ACTA-01', ultimo_moderno_id: 0 }
    const w = await detalle()
    await w.get('button.btn-primary.mt-4').trigger('click')
    await w.findAll('select')[0].setValue('Ventas')
    await w.get('#receptor-operacion').setValue('Centro Cultural')
    await w.get('#tipo-receptor-operacion').setValue('INSTITUCION')
    await w.get('#movimiento-referencia').setValue('FACT-10')
    await w.get('input[type="number"]').setValue(10)
    post.mockRejectedValueOnce({ response: { status: 409, data: { detail: {
      codigo: 'ALERTAS_CONTROL', firma_confirmacion: 'a'.repeat(64),
      alertas: [{ codigo: 'AGOTA_STOCK', nivel: 'alto',
        mensaje: 'La salida dejará el artículo sin existencias.' }]
    } } } }).mockResolvedValueOnce({ data: { saldo_registrado: 0 } })
    await w.get('.actions button').trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledTimes(1)
    const primeraSolicitud = post.mock.calls[0][1].solicitud_id
    expect(primeraSolicitud).toMatch(/^[0-9a-f-]{36}$/)
    expect(w.text()).toContain('La salida dejará el artículo sin existencias.')
    await w.get('.actions button').trigger('click')
    expect(post).toHaveBeenCalledTimes(1)
    await w.get('#motivo-alertas').setValue('Salida autorizada mediante acta')
    await w.get('.actions button').trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/kardex/movimiento-actual',
      expect.objectContaining({ cantidad: 10, confirmacion_alertas: 'a'.repeat(64),
        motivo_alertas: 'Salida autorizada mediante acta',
        referencia_documento: 'FACT-10', fecha_operacion: expect.any(String) }))
    expect(post.mock.calls[1][1].solicitud_id).toBe(primeraSolicitud)
    expect(w.text()).toContain('Transacción registrada correctamente.')
    w.unmount()
  })
  it('permite revisar una confirmación caducada sin crear otra solicitud', async () => {
    articulo.stock_actual = 10
    articulo.apertura = { cantidad_inicial: 10, aprobado_en: '2026-10-06T20:00:00Z',
      referencia_documento: 'ACTA-01', ultimo_moderno_id: 0 }
    const w = await detalle()
    await w.get('button.btn-primary.mt-4').trigger('click')
    await w.findAll('select')[0].setValue('Ventas')
    await w.get('#receptor-operacion').setValue('Biblioteca')
    await w.get('#tipo-receptor-operacion').setValue('INSTITUCION')
    await w.get('#movimiento-referencia').setValue('FACT-REPETIDA')
    post.mockRejectedValueOnce({ response: { status: 409, data: { detail: {
      codigo: 'ALERTAS_CONTROL', firma_confirmacion: 'a'.repeat(64),
      alertas: [{ codigo: 'POSIBLE_DUPLICADO', nivel: 'medio', mensaje: 'Posible repetición.' }]
    } } } }).mockRejectedValueOnce({ response: { status: 409, data: { detail: {
      codigo: 'CONTROL_DESACTUALIZADO', mensaje: 'Vuelve a revisar la operación.'
    } } } }).mockResolvedValueOnce({ data: { saldo_registrado: 9 } })
    await w.get('.actions button').trigger('click'); await flushPromises()
    const solicitud = post.mock.calls[0][1].solicitud_id
    await w.get('#motivo-alertas').setValue('Entrega parcial con el mismo comprobante verificada')
    await w.get('.actions button').trigger('click'); await flushPromises()
    expect(post).toHaveBeenCalledTimes(2)
    expect(w.find('#motivo-alertas').exists()).toBe(false)
    expect(w.text()).toContain('Vuelve a revisar la operación.')
    await w.get('.actions button').trigger('click'); await flushPromises()
    expect(post.mock.calls[2][1]).toEqual(expect.objectContaining({ solicitud_id: solicitud,
      confirmacion_alertas: null, motivo_alertas: '' }))
    expect(w.text()).toContain('Transacción registrada correctamente.')
    w.unmount()
  })
})
async function detalle() {
  const w = mount(InventarioActualView, { global: { stubs: { RouterLink: RouterLinkStub } } })
  await flushPromises()
  await w.get('.articulo-card').trigger('click')
  await flushPromises()
  return w
}
describe('Correcciones operativas', () => {
  it('rectifica desde el historial y registra un ajuste con documento', async () => {
    articulo.stock_actual = 8
    articulo.apertura = { cantidad_inicial: 10, cantidad_actual: 8,
      aprobado_en: '2026-10-06T20:00:00Z', referencia_documento: 'ACTA-01',
      ultimo_moderno_id: 0, origen: 'CONTEO_FISICO' }
    const original = { id: 21, tipo_operacion: 'Ventas', estado: 'ACTIVO',
      salidas: 2, ingresos: null, saldo_registrado: 8, area_operativa_id: 2,
      referencia_documento: 'FACT-01', corrige_movimiento_id: null }
    let movimientos: Record<string, unknown>[] = [original]
    get.mockImplementation((url: string) => Promise.resolve({ data:
      url === '/kardex/articulos' ? [{ ...articulo }] :
      url === '/kardex/historial-actual/1' ? movimientos :
      url === '/kardex/areas-operativas' ? [{ id: 2, nombre: 'Galería' }] :
      url === '/kardex/encargados' ? [{ id: 1, nombre: 'Encargada' }] :
      url.includes('/existencias-area') ? { total_institucional: articulo.stock_actual,
        sin_ubicacion_confirmada: 0, en_custodia_externa: 0,
        areas: [{ area_id: 2, area: 'Galería', cantidad: (articulo.stock_actual ?? 0) - 4 }],
        estado: 'DISTRIBUCION_COMPLETA' } :
      url.includes('/conciliacion-inicial') ? { estado: 'NO_DISPONIBLE' } : [] }))
    post.mockImplementation((url: string) => {
      articulo.stock_actual = url.includes('/corregir') ? 9 : 10
      movimientos = [...movimientos, { ...original, id: movimientos.length + 21,
        tipo_operacion: url.includes('/corregir') ? 'Rectificación operativa' : 'Ajuste operativo',
        corrige_movimiento_id: url.includes('/corregir') ? 21 : null,
        cantidad_anterior: 2, cantidad_corregida: 1, ingresos: 1, salidas: null,
        saldo_registrado: articulo.stock_actual }]
      return Promise.resolve({ data: { saldo_registrado: articulo.stock_actual } })
    })
    const w = await detalle()
    await w.get('button[aria-label="Rectificar movimiento 21"]').trigger('click')
    const correccion = w.get('form[aria-label="Rectificar cantidad registrada"]')
    await correccion.get('#correccion-cantidad').setValue(1)
    await correccion.get('#correccion-motivo').setValue('Cantidad comprobada en el acta')
    await correccion.get('#correccion-documento').setValue('ACTA-COR-01')
    await correccion.trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/kardex/movimiento-actual/21/corregir',
      expect.objectContaining({ cantidad_corregida: 1,
        motivo: 'Cantidad comprobada en el acta', referencia_documento: 'ACTA-COR-01' }))
    expect(w.text()).toContain('Rectifica movimiento #21')
    const ajuste = w.get('form[aria-label="Registrar ajuste operativo"]')
    await ajuste.get('#ajuste-area').setValue('2')
    await ajuste.get('#ajuste-motivo').setValue('Diferencia comprobada por recuento')
    await ajuste.get('#ajuste-documento').setValue('ACTA-AJU-01')
    await ajuste.trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/kardex/articulos/1/ajustes-operativos',
      expect.objectContaining({ direccion: 'ingreso', cantidad: 1,
        area_id: 2, motivo: 'Diferencia comprobada por recuento' }))
    w.unmount()
  })
})
describe('Apertura del inventario', () => {
  it('muestra feria y consignación como custodia y registra una venta solo desde la entrega', async () => {
    articulo.stock_actual = 10
    articulo.apertura = { cantidad_inicial: 10, cantidad_actual: 10,
      aprobado_en: '2026-10-06T20:00:00Z', referencia_documento: 'ACTA-01',
      ultimo_moderno_id: 0, origen: 'CONTEO_FISICO' }
    let distribucion = { total_institucional: 10, sin_ubicacion_confirmada: 0,
      en_custodia_externa: 0, areas: [{ area_id: 2, area: 'Galería', cantidad: 6 },
        { area_id: 3, area: 'Depósito', cantidad: 4 }], estado: 'DISTRIBUCION_COMPLETA' }
    let custodias: Record<string, unknown>[] = []
    let vistaPreviaEntrega = true
    get.mockImplementation((url: string) => Promise.resolve({ data:
      url === '/kardex/articulos' ? [{ ...articulo }] :
      url === '/kardex/areas-operativas' ? [{ id: 2, nombre: 'Galería' }, { id: 3, nombre: 'Depósito' }] :
      url === '/kardex/encargados' ? [{ id: 1, nombre: 'Encargada' }] :
      url === '/kardex/articulos/1/custodias-externas' ? custodias :
      url.includes('/existencias-area') ? distribucion :
      url.includes('/conciliacion-inicial') ? { estado: 'NO_DISPONIBLE', motivo: 'Sin conteo inicial' } : [] }))
    post.mockImplementation((url: string) => {
      if (url === '/kardex/articulos/1/custodias-externas') {
        if (vistaPreviaEntrega) {
          vistaPreviaEntrega = false
          return Promise.reject({ response: { status: 409, data: { detail: {
            codigo: 'ALERTAS_CONTROL', firma_confirmacion: 'b'.repeat(64),
            alertas: [{ codigo: 'CANTIDAD_EXTREMA', nivel: 'alto',
              mensaje: 'Verifica la cantidad entregada.' }]
          } } } })
        }
        custodias = [{ id: 7, tipo: 'FERIA', estado: 'ABIERTA', area_origen: 'Galería',
          receptor_nombre: 'Centro Cultural', receptor_tipo: 'INSTITUCION',
          ubicacion_externa: 'Feria del Libro', ciudad: 'Cochabamba',
          cantidad_entregada: 3, cantidad_fuera: 3, cantidad_vendida: 0, cantidad_devuelta: 0,
          referencia_documento: 'ACTA-ENTREGA', ocurrido_en: '2026-10-08T15:00:00Z',
          registrado_en: '2026-10-08T15:00:00Z', encargado_id: 1, registrado_por: 1, eventos: [] }]
        distribucion = { ...distribucion, en_custodia_externa: 3,
          areas: [{ area_id: 2, area: 'Galería', cantidad: 3 },
            { area_id: 3, area: 'Depósito', cantidad: 4 }] }
        return Promise.resolve({ data: { registro: custodias[0], distribucion } })
      }
      articulo.stock_actual = 9
      custodias[0] = { ...custodias[0], cantidad_fuera: 2, cantidad_vendida: 1,
        eventos: [{ id: 9, tipo: 'VENTA', cantidad: 1, comprador: 'Biblioteca',
          referencia_documento: 'FACT-01', ocurrido_en: '2026-10-08T15:30:00Z' }] }
      distribucion = { ...distribucion, total_institucional: 9, en_custodia_externa: 2 }
      return Promise.resolve({ data: { registro: { id: 9 }, custodia: custodias[0], distribucion } })
    })
    const w = await detalle()
    const form = w.get('form[aria-label="Registrar entrega externa"]')
    await form.get('#custodia-origen').setValue('2')
    await form.get('#custodia-receptor').setValue('Centro Cultural')
    await form.get('#custodia-ubicacion').setValue('Feria del Libro')
    await form.get('#custodia-ciudad').setValue('Cochabamba')
    await form.get('#custodia-cantidad').setValue(3)
    await form.get('#custodia-documento').setValue('ACTA-ENTREGA')
    await form.trigger('submit')
    await flushPromises()
    expect(custodias).toHaveLength(0)
    expect(w.text()).toContain('Verifica la cantidad entregada.')
    const solicitudInicial = post.mock.calls[0][1].solicitud_id
    await form.get('#custodia-motivo-alertas').setValue('Entrega autorizada por acta')
    await form.trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/kardex/articulos/1/custodias-externas',
      expect.objectContaining({ tipo: 'FERIA', area_origen_id: 2,
        cantidad: 3, receptor_nombre: 'Centro Cultural', solicitud_id: solicitudInicial,
        confirmacion_alertas: 'b'.repeat(64),
        motivo_alertas: 'Entrega autorizada por acta' }))
    expect(w.text()).toContain('En custodia externa: 3 u.')
    expect(w.text()).toContain('Total institucional: 10 u.')
    const evento = w.get('form[aria-label="Registrar venta o retorno de entrega 7"]')
    await evento.get('#evento-tipo-7').setValue('VENTA')
    await evento.get('#evento-comprador-7').setValue('Biblioteca')
    await evento.get('#evento-documento-7').setValue('FACT-01')
    await evento.trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/kardex/articulos/1/custodias-externas/7/eventos',
      expect.objectContaining({ tipo: 'VENTA', cantidad: 1, comprador: 'Biblioteca',
        area_destino_id: null, referencia_documento: 'FACT-01' }))
    expect(w.text()).toContain('En custodia externa: 2 u.')
    expect(w.text()).toContain('Total institucional: 9 u.')
    w.unmount()
  })
  it('muestra el libro digital con base, traslado y saldo institucional', async () => {
    articulo.stock_actual = 12
    articulo.apertura = { cantidad_inicial: 10, cantidad_actual: 12,
      aprobado_en: '2026-10-06T20:00:00Z', referencia_documento: 'ACTA-01',
      ultimo_moderno_id: 0, origen: 'CONTEO_FISICO' }
    get.mockImplementation((url: string) => Promise.resolve({ data:
      url === '/kardex/articulos' ? [{ ...articulo }] :
      url === '/kardex/articulos/1/kardex-digital' ? {
        estado: 'OPERATIVO', base: { cantidad: 10, origen: 'CONTEO_FISICO',
          movimiento_historico_id: null, lote_historico_id: null,
          fecha_corte: '2026-10-06T20:00:00Z', referencia_documento: 'ACTA-01' },
        saldo_final: 12, integridad: true,
        eventos: [{ clase: 'TRANSFERENCIA', id: 4,
          fecha_operacion: '2026-10-08T14:00:00Z', fecha_documental: null,
          fecha_registro: '2026-10-08T14:05:00Z', descripcion: 'Transferencia entre áreas',
          ingreso: 0, salida: 0, cantidad_original: 3, cantidad_transferida: 3,
          area_origen: 'Galería', area_destino: 'Depósito', documento: 'ACTA-02',
          encargado: 'Encargada', registrador: 'Operadora', receptor: null,
          estado: 'ACTIVO', saldo_institucional: 12 }] } :
      url.includes('/conciliacion-inicial') ? { estado: 'NO_DISPONIBLE', motivo: 'Sin conteo inicial' } :
      url.includes('/existencias-area') ? { total_institucional: 12, sin_ubicacion_confirmada: 12,
        areas: [], estado: 'DISTRIBUCION_PARCIAL' } : [] }))
    const w = await detalle()
    const libro = w.get('section[aria-label="Kárdex digital por artículo"]')
    expect(libro.text()).toContain('Base: 10 u.')
    expect(libro.text()).toContain('Saldo calculado: 12 u.')
    expect(libro.text()).toContain('Galería → Depósito')
    expect(libro.text()).toContain('3 u. trasladadas')
    expect(libro.text()).toContain('ACTA-02')
    w.unmount()
  })
  it('transfiere entre dos áreas sin cambiar el total mostrado', async () => {
    articulo.stock_actual = 10
    articulo.apertura = { cantidad_inicial: 10, cantidad_actual: 10,
      aprobado_en: '2026-10-06T20:00:00Z', referencia_documento: 'ACTA-01',
      ultimo_moderno_id: 0, origen: 'CONTEO_FISICO' }
    const distribucion = { total_institucional: 10, sin_ubicacion_confirmada: 0,
      areas: [{ area_id: 2, area: 'Galería', cantidad: 6 },
        { area_id: 3, area: 'Depósito', cantidad: 4 }], estado: 'DISTRIBUCION_COMPLETA' }
    get.mockImplementation((url: string) => Promise.resolve({ data:
      url === '/kardex/articulos' ? [{ ...articulo }] :
      url === '/kardex/areas-operativas' ? [{ id: 2, nombre: 'Galería' }, { id: 3, nombre: 'Depósito' }] :
      url === '/kardex/encargados' ? [{ id: 1, nombre: 'Encargada' }] :
      url.includes('/existencias-area') ? distribucion :
      url.includes('/conciliacion-inicial') ? { estado: 'NO_DISPONIBLE', motivo: 'Sin conteo inicial' } : [] }))
    post.mockRejectedValueOnce({ response: { status: 409, data: { detail: {
      codigo: 'ALERTAS_CONTROL', firma_confirmacion: 'b'.repeat(64),
      alertas: [{ codigo: 'POSIBLE_DUPLICADO', nivel: 'medio', mensaje: 'Revisa el posible registro repetido.' }]
    } } } }).mockResolvedValue({ data: { registro: { id: 5 }, distribucion: {
      ...distribucion, areas: [{ area_id: 2, area: 'Galería', cantidad: 3 },
        { area_id: 3, area: 'Depósito', cantidad: 7 }] } } })
    const w = await detalle()
    const form = w.get('form[aria-label="Transferir entre áreas"]')
    await form.get('#transferencia-origen').setValue('2')
    await form.get('#transferencia-destino').setValue('3')
    await form.get('#transferencia-cantidad').setValue(3)
    await form.get('#transferencia-documento').setValue('ACTA-TRASLADO')
    await form.get('#transferencia-fecha').setValue('2026-10-08T11:00')
    await form.trigger('submit')
    await flushPromises()
    const solicitud = post.mock.calls[0][1].solicitud_id
    expect(form.text()).toContain('Revisa el posible registro repetido')
    await form.trigger('submit'); await flushPromises()
    expect(post).toHaveBeenCalledTimes(1)
    await form.get('#transferencia-motivo-alertas').setValue('Segundo traslado parcial con la misma acta verificado')
    await form.trigger('submit'); await flushPromises()
    expect(post).toHaveBeenCalledWith('/kardex/articulos/1/transferencias',
      expect.objectContaining({ area_origen_id: 2, area_destino_id: 3,
        cantidad: 3, fecha_operacion: '2026-10-08T15:00:00.000Z',
        referencia_documento: 'ACTA-TRASLADO', solicitud_id: expect.any(String) }))
    expect(w.text()).toContain('Total institucional: 10 u.')
    expect(w.text()).toContain('Galería: 3 u.')
    expect(w.text()).toContain('Depósito: 7 u.')
    expect(post.mock.calls[1][1]).toEqual(expect.objectContaining({ solicitud_id: solicitud,
      confirmacion_alertas: 'b'.repeat(64), motivo_alertas: 'Segundo traslado parcial con la misma acta verificado' }))
    w.unmount()
  })
  it('concilia un conteo total por área y muestra el ajuste documentado', async () => {
    articulo.stock_actual = 10
    articulo.base_kardex = { saldo: 10, movimiento_id: 7, lote_id: 3,
      fecha_movimiento: '2025-12-31', operable: true, motivo_bloqueo: null }
    get.mockImplementation((url: string) => Promise.resolve({ data:
      url === '/kardex/articulos' ? [{ ...articulo }] :
      url === '/kardex/areas-operativas' ? [{ id: 2, nombre: 'Galería' }] :
      url === '/kardex/encargados' ? [{ id: 1, nombre: 'Encargada' }] :
      url.includes('/conciliacion-inicial') ? { estado: 'DISPONIBLE', cantidad_base: 10 } :
      url.includes('/existencias-area') ? { total_institucional: 10, sin_ubicacion_confirmada: 10, areas: [], estado: 'BASE_DOCUMENTAL_SIN_DISTRIBUIR' } : [] }))
    post.mockResolvedValue({ data: { registro: { cantidad_base: 10, cantidad_fisica: 8,
      diferencia: -2, fecha_conteo: '2026-10-08', referencia_documento: 'ACTA-03',
      justificacion: 'Conteo total verificado', ajuste_movimiento_id: 9,
      areas: [{ area_id: 2, area: 'Galería', cantidad: 8 }] },
      distribucion: { total_institucional: 8, sin_ubicacion_confirmada: 0,
        areas: [{ area_id: 2, area: 'Galería', cantidad: 8 }], estado: 'DISTRIBUCION_COMPLETA' } } })
    const w = await detalle()
    await w.get('#conteo-area-2').setValue(8)
    await w.get('#conteo-encargado').setValue('1')
    await w.get('#conteo-documento').setValue('ACTA-03')
    await w.get('#conteo-justificacion').setValue('Conteo total verificado')
    await w.findAll('input[type="checkbox"]')[0].setValue(true)
    await w.findAll('input[type="checkbox"]')[1].setValue(true)
    await w.find('section[aria-label="Conciliación inicial"] form').trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/kardex/articulos/1/conciliacion-inicial',
      expect.objectContaining({ areas: [{ area_id: 2, cantidad: 8 }],
        alcance_total: true, conteo_verificado: true }))
    expect(w.text()).toContain('diferencia: -2 u.')
    expect(w.text()).toContain('Ajuste registrado como movimiento #9')
    w.unmount()
  })
  it('muestra la distribución y registra una ubicación sin cambiar el total', async () => {
    articulo.stock_actual = 10
    articulo.apertura = { cantidad_inicial: 10, cantidad_actual: 10, aprobado_en: '2026-10-06T20:00:00Z',
      referencia_documento: 'ACTA-01', ultimo_moderno_id: 0, origen: 'CONTEO_FISICO' }
    get.mockImplementation((url: string) => Promise.resolve({ data:
      url === '/kardex/articulos' ? [{ ...articulo }] :
      url === '/kardex/areas-operativas' ? [{ id: 2, nombre: 'Galería' }] :
      url === '/kardex/encargados' ? [{ id: 1, nombre: 'Encargada' }] :
      url.includes('/conciliacion-inicial') ? { estado: 'NO_DISPONIBLE', motivo: 'Sin conteo inicial' } :
      url.includes('/existencias-area') ? { total_institucional: 10, sin_ubicacion_confirmada: 10, areas: [], estado: 'DISTRIBUCION_PARCIAL' } : [] }))
    post.mockResolvedValue({ data: { total_institucional: 10, sin_ubicacion_confirmada: 6,
      areas: [{ area_id: 2, area: 'Galería', cantidad: 4 }], estado: 'DISTRIBUCION_PARCIAL' } })
    const w = await detalle()
    expect(w.text()).toContain('Sin ubicación confirmada: 10 u.')
    await w.get('#asignacion-area').setValue('2')
    await w.get('#asignacion-cantidad').setValue(4)
    await w.get('#asignacion-encargado').setValue('1')
    await w.get('#asignacion-documento').setValue('ACTA-02')
    await w.get('#asignacion-justificacion').setValue('Ubicación verificada en sala')
    await w.get('form').trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/kardex/articulos/1/asignar-area',
      expect.objectContaining({ area_id: 2, cantidad: 4, encargado_id: 1 }))
    expect(w.text()).toContain('Sin ubicación confirmada: 6 u.')
    expect(w.text()).toContain('Galería: 4 u.')
    w.unmount()
  })
  it('muestra el último saldo escaneado y permite iniciar una operación sin apertura manual', async () => {
    articulo.stock_actual = 18
    articulo.base_kardex = { saldo: 18, movimiento_id: 27, lote_id: 4,
      fecha_movimiento: '2025-12-31', operable: true, motivo_bloqueo: null }
    const w = await detalle()
    expect(w.text()).toContain('Saldo final escaneado')
    expect(w.text()).toContain('Base de trabajo del Kárdex histórico: 18 u.')
    expect(w.text()).toContain('+ Nueva Transacción')
    expect(w.find('form').exists()).toBe(false)
    w.unmount()
  })
  it('muestra la alerta del cierre y bloquea operaciones hasta revisarlo', async () => {
    articulo.stock_actual = 7
    articulo.base_kardex = { saldo: 7, movimiento_id: 27, lote_id: 4,
      fecha_movimiento: '2025-12-31', operable: false,
      motivo_bloqueo: 'El saldo final tiene una alerta matemática pendiente de revisión.' }
    const w = await detalle()
    expect(w.text()).toContain('alerta matemática pendiente')
    expect(w.text()).not.toContain('+ Nueva Transacción')
    w.unmount()
  })
  it('no representa una apertura pendiente como cero ni permite operaciones', async () => {
    const w = await detalle()
    expect(w.text()).toContain('Sin apertura')
    expect(w.text()).not.toContain('+ Nueva Transacción')
    expect(w.get('button[type="submit"]').attributes('disabled')).toBeDefined()
    w.unmount()
  })
  it.each(['Operador', 'Auditor'])('no ofrece aprobar la apertura al %s', async rol => {
    auth.rol = rol
    const w = await detalle()
    expect(w.find('form').exists()).toBe(false)
    expect(w.text()).toContain('Un administrador debe aprobar')
    w.unmount()
  })
  it('aprueba un conteo cero con evidencia y habilita operaciones', async () => {
    const w = await detalle()
    await w.get('#apertura-referencia').setValue('ACTA-01')
    await w.get('#apertura-justificacion').setValue('Conteo físico verificado')
    await w.get('input[type="checkbox"]').setValue(true)
    post.mockResolvedValue({ data: { cantidad_inicial: 0, cantidad_actual: 0, ultimo_moderno_id: 0, aprobado_por: 1, aprobado_en: '2026-10-06T20:00:00Z', referencia_documento: 'ACTA-01' } })
    await w.get('form').trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/kardex/articulos/1/apertura', expect.objectContaining({ cantidad: 0, conteo_verificado: true }))
    expect(w.text()).toContain('+ Nueva Transacción')
    expect(w.text()).toContain('Apertura aprobada: 0 u.')
    w.unmount()
  })
  it('no permite aprobar dos veces mientras espera respuesta y muestra errores', async () => {
    const w = await detalle()
    let rechazar!: (error: unknown) => void
    post.mockImplementation(() => new Promise((_, reject) => { rechazar = reject }))
    await w.get('form').trigger('submit')
    await w.get('form').trigger('submit')
    expect(post).toHaveBeenCalledTimes(1)
    rechazar({ response: { data: { detail: 'El artículo ya tiene una apertura aprobada.' } } })
    await flushPromises()
    expect(w.text()).toContain('El artículo ya tiene una apertura aprobada.')
    w.unmount()
  })
  it('el auditor consulta stock aprobado sin acciones de escritura', async () => {
    auth.rol = 'Auditor'
    articulo.stock_actual = 5
    articulo.apertura = { cantidad_inicial: 5, aprobado_en: '2026-10-06T20:00:00Z', referencia_documento: 'ACTA-01', ultimo_moderno_id: 1 }
    const w = await detalle()
    expect(w.text()).toContain('Apertura aprobada: 5 u.')
    expect(w.text()).not.toContain('+ Nueva Transacción')
    expect(w.text()).not.toContain('Aprobar saldo de apertura')
    w.unmount()
  })
})
