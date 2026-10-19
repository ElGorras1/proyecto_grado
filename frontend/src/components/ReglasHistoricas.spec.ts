import {mount, flushPromises, RouterLinkStub} from '@vue/test-utils'
import {beforeEach, afterEach, describe, it, expect, vi} from 'vitest'
import ReglasHistoricas from './ReglasHistoricas.vue'

const {get} = vi.hoisted(() => ({get: vi.fn()}))
vi.mock('@/services/api', () => ({default: {get, defaults: {baseURL:'http://localhost:8000/api/v1'}}}))
const politica = {version:'2026-10-14.1', limites:['No se documenta hora histórica.'],
  cantidad_extrema:1000, porcentaje_mayoritario:80, factor_atipico:3, min_comparables:5,
  reglas:[{codigo:'AGOTA_STOCK',nombre:'Salida de todas las unidades'}]}
const fila = {id:2, articulo_id:4, articulo:'Libro histórico', codigo:'L-4', fecha:'2025-01-01',
  fecha_estimada:false, ingresos:null, salidas:10, saldo_previo:10, saldo_vigente:0,
  base_utilizable:true, saldo_esperado_reglas:0, movimiento_previo_id:1,
  lote_id:3, tanda:1, numero_pagina:1, orden_fila:2, detalle:'Donación',
  ruta_imagen_respaldo:'storage/kardex_images/hoja.webp', revision_documental:null,
  avisos:[{codigo:'AGOTA_STOCK',nombre:'Salida de todas las unidades',nivel:'alto',mensaje:'Retiro de todas las unidades.',datos:{saldo_previo:10}}],
  no_evaluables:[], observado:false}
const resultado = {total:61,filas:[fila],politica,resumen:{con_avisos:61,evaluacion_parcial:2,consultado_en:'2026-10-14'}}
vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
const createUrl = vi.fn(() => 'blob:historico'), revokeUrl = vi.fn()
beforeEach(() => {
  get.mockReset(); createUrl.mockClear(); revokeUrl.mockClear()
  Object.defineProperty(URL,'createObjectURL',{configurable:true,value:createUrl})
  Object.defineProperty(URL,'revokeObjectURL',{configurable:true,value:revokeUrl})
  get.mockImplementation((url:string) => {
    if (url.endsWith('/opciones')) return Promise.resolve({data:{gestiones:[2025,2024],politica}})
    if (url.endsWith('/2')) return Promise.resolve({data:{fila,vecinos:[fila],datos_originales:{saldo_registrado:0}}})
    if (url.endsWith('.csv')) return Promise.resolve({data:'ID;Reglas\n2;AGOTA_STOCK\n'})
    return Promise.resolve({data:resultado})
  })
})
afterEach(() => {vi.clearAllMocks()})
function montar() { return mount(ReglasHistoricas,{props:{gestionInicial:'2025'},global:{stubs:{RouterLink:RouterLinkStub}}}) }
describe('Reglas históricas', () => {
  it('consulta el histórico por gestión sin depender de un modelo ni registrar operaciones', async () => {
    const w=montar(); await flushPromises()
    expect(get).toHaveBeenCalledWith('/analitica/reglas-historicas',expect.objectContaining({params:expect.objectContaining({gestion:2025,seleccion:'avisos'})}))
    expect(w.text()).toContain('Salida de todas las unidades')
    expect(w.text()).toContain('No se documenta hora histórica.')
    expect(get.mock.calls.every(([url])=>!url.includes('/modelos'))).toBe(true)
    w.unmount()
  })
  it('conserva la edición durante una consulta y usa filtros aplicados al paginar', async () => {
    const w=montar(); await flushPromises()
    const original=get.getMockImplementation()!
    let resolver!:(v:unknown)=>void
    get.mockImplementation((url:string,opts: { params: Record<string, string | number> })=>url.endsWith('/reglas-historicas') && opts.params.articulo==='Primero' && opts.params.pagina===1
      ? new Promise(r=>{resolver=r}) : original(url,opts))
    await w.get('[aria-label="Artículo de reglas históricas"]').setValue('  Primero  ')
    await w.get('form').trigger('submit')
    await w.get('[aria-label="Artículo de reglas históricas"]').setValue('Segundo')
    resolver({data:resultado}); await flushPromises()
    expect(w.text()).toContain('sin aplicar')
    const next=w.findAll('button').find(b=>b.text()==='Reglas siguientes')!
    await next.trigger('click'); await flushPromises()
    expect(get).toHaveBeenLastCalledWith('/analitica/reglas-historicas',expect.objectContaining({params:expect.objectContaining({articulo:'Primero',pagina:2})}))
    expect((w.get('[aria-label="Artículo de reglas históricas"]').element as HTMLInputElement).value).toBe('Segundo')
    w.unmount()
  })
  it('abre foto, reglas y contexto y enlaza a la revisión HIL del artículo', async () => {
    const w=montar(); await flushPromises()
    await w.findAll('button').find(b=>b.text()==='Ver detalle de reglas')!.trigger('click'); await flushPromises()
    const detail=w.get('[aria-label="Evidencia de reglas históricas"]')
    expect(detail.get('img').attributes('src')).toBe('http://localhost:8000/storage/kardex_images/hoja.webp')
    expect(detail.text()).toContain('Extracción original conservada')
    expect(detail.text()).toContain('Filas anteriores y siguientes')
    expect(detail.findComponent(RouterLinkStub).props('to')).toEqual({path:'/kardex-digital',query:{articulo_id:4,tab:'hil'}})
    w.unmount()
  })
  it('exporta la última consulta aplicada aunque haya cambios pendientes', async () => {
    const w=montar(); await flushPromises()
    await w.get('[aria-label="Gestión de reglas históricas"]').setValue('2024')
    await w.findAll('button').find(b=>b.text()==='Descargar reglas históricas (CSV)')!.trigger('click'); await flushPromises()
    expect(get).toHaveBeenLastCalledWith('/analitica/reglas-historicas.csv',expect.objectContaining({params:expect.objectContaining({gestion:2025}),responseType:'blob'}))
    expect(createUrl).toHaveBeenCalled(); expect(revokeUrl).toHaveBeenCalledWith('blob:historico')
    w.unmount()
  })
  it('distingue falla de consulta de cero resultados y permite reintentar', async () => {
    get.mockImplementation((url:string)=>url.endsWith('/opciones')
      ? Promise.resolve({data:{gestiones:[2025],politica}}) : Promise.reject(new Error('Sin red')))
    const w=montar(); await flushPromises()
    expect(w.text()).toContain('No se pudieron consultar las reglas históricas')
    expect(w.text()).not.toContain('No hay movimientos para los filtros')
    expect(w.findAll('button').some(b=>b.text()==='Reintentar revisión histórica')).toBe(true)
    w.unmount()
  })
})
