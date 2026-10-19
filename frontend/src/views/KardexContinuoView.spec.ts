import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import KardexContinuoView from './KardexContinuoView.vue'
const { get, post, auth } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), auth: { rol: 'Administrador' } }))
vi.mock('@/services/api', () => ({ default: { get, post, defaults: { baseURL: 'http://localhost:8000/api/v1' } } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
vi.mock('vue-router', () => ({ useRoute: () => ({ query: {} }) }))
const filas = [1, 2].map(tanda => ({ id: tanda, lote_id: tanda, tanda, fecha_movimiento: '2025-01-01', detalle: `Documento tanda ${tanda}`, ingresos: 5, salidas: null, saldo_registrado: 5, tiene_error_saldo: true, tipos_alerta: ['saldo'], numero_pagina: 1 }))
beforeEach(() => {
 auth.rol = 'Administrador'
 get.mockReset(); post.mockReset()
 get.mockImplementation((url: string) => {
   if(url === '/kardex/tandas') return Promise.resolve({ data: { tanda_nuevas_cargas: 2, tandas: [1, 2].map(id => ({ id, nombre: `Tanda ${id}`, movimientos: 1, escaneos: 1 })) } })
   if(url === '/kardex/articulos') return Promise.resolve({ data: [{ id:1, nombre:'Libro', codigo:'QA', alertas_rojas:2, alertas_amarillas:0 }] })
   if(url === '/kardex/limites-carga') return Promise.resolve({ data: { paginas:20, mb_imagen:20, mb_lote:100 } })
   return Promise.resolve({ data: filas })
 })
})
async function montar() {
 const w = mount(KardexContinuoView, { global: { stubs: { RouterLink: RouterLinkStub, TrazabilidadArticulo:true, RevisionHil:true } } })
 await flushPromises()
 await w.get('.articulo-card').trigger('click'); await flushPromises()
 return w
}
describe('Archivo por tandas', () => {
 it('distingue avisos categorizados y filtra por su tratamiento sin ocultarlos por defecto', async () => {
   const anterior = get.getMockImplementation()!
   get.mockImplementation((url: string) => {
     if (url.includes('/historial/') || url.includes('/errores')) return Promise.resolve({ data: [
       { ...filas[0], revision_documental: { motivo: 'La diferencia del papel se conserva.' }, tratamiento_hil: {
         estado: 'CATEGORIZADO_CON_MARCA', etiqueta: 'Categorizado con marca', categorias: ['DISCREPANCIA_DOCUMENTAL'],
         decisiones: [{ campo:'saldo', categoria:'DISCREPANCIA_DOCUMENTAL', etiqueta:'Discrepancia del documento', motivo:'Saldo escrito 8, cálculo 7; diferencia conservada.', criterios:['T05'] }],
         datos_confirmados:false, habilita_entrenamiento:false,
       } }, filas[1],
     ] })
     return anterior(url)
   })
   const w = await montar()
   await w.findAll('.tabs .tab-btn')[1].trigger('click'); await flushPromises()
   expect(w.findAll('.tabla-errores tbody tr')).toHaveLength(2)
   expect(w.text()).toContain('1 categorizados con marca · 1 por categorizar o actualizar')
   expect(w.get('.marca-documental').text()).toContain('no equivalen a datos confirmados')
   const filtros = w.findAll('.hil-filtros select')
   await filtros[2].setValue('DISCREPANCIA_DOCUMENTAL')
   expect(w.findAll('.tabla-errores tbody tr')).toHaveLength(1)
   expect(w.get('.tabla-errores').text()).toContain('Documento tanda 1')
   await filtros[0].setValue('fecha')
   expect(w.findAll('.tabla-errores tbody tr')).toHaveLength(0)
   await filtros[0].setValue(''); await filtros[2].setValue('')
   await filtros[1].setValue('POR_CATEGORIZAR')
   expect(w.get('.tabla-errores').text()).toContain('Documento tanda 2')
   expect(w.get('.tabla-errores').text()).not.toContain('Documento tanda 1')
   await filtros[1].setValue('')
   expect(w.findAll('.tabla-errores tbody tr')).toHaveLength(2)
   expect(post).not.toHaveBeenCalled()
   w.unmount()
 })
 it('consulta la tercera tanda y obtiene la tanda de nuevas cargas del servidor', async () => {
   const anterior = get.getMockImplementation()!
   get.mockImplementation((url: string) => {
     if (url === '/kardex/tandas') return Promise.resolve({ data: {
       tanda_nuevas_cargas: 3,
       tandas: [1, 2, 3].map(id => ({ id, nombre: `Tanda ${id}`, movimientos: 1, escaneos: 1 }))
     } })
     if (url.includes('/historial/') || url.includes('/errores')) return Promise.resolve({ data: [
       ...filas, { ...filas[0], id: 3, lote_id: 3, tanda: 3, detalle: 'Documento tanda 3' }
     ] })
     return anterior(url)
   })
   const w = await montar()
   await w.findAll('.tandas-controles button')[3].trigger('click')
   expect(w.findAll('.tabla-kardex tbody tr')).toHaveLength(1)
   expect(w.get('.tabla-kardex').text()).toContain('Documento tanda 3')
   await w.get('.with-action button').trigger('click')
   expect(w.text()).toContain('Subir Fotografías del Kárdex · Tanda 3')
   expect(post).not.toHaveBeenCalled()
   w.unmount()
 })
 it('muestra ambas tandas y permite consultar cada una sin modificar datos', async () => {
   const w=await montar()
   expect(w.findAll('.tabla-kardex tbody tr')).toHaveLength(2)
   await w.findAll('.tandas-controles button')[1].trigger('click')
   expect(w.findAll('.tabla-kardex tbody tr')).toHaveLength(1)
   expect(w.get('.tabla-kardex').text()).toContain('Documento tanda 1')
   expect(w.get('.tabla-kardex').text()).not.toContain('Documento tanda 2')
   await w.findAll('.tandas-controles button')[2].trigger('click')
   expect(w.get('.tabla-kardex').text()).toContain('Documento tanda 2')
   await w.findAll('.tandas-controles button')[0].trigger('click')
   expect(w.findAll('.tabla-kardex tbody tr')).toHaveLength(2)
   expect(post).not.toHaveBeenCalled()
   w.unmount()
 })
 it('filtra revisión HIL y ofrece trazabilidad histórica con filtros propios', async () => {
   const w=await montar()
   await w.findAll('.tandas-controles button')[1].trigger('click')
   await w.findAll('.tabs .tab-btn')[1].trigger('click'); await flushPromises()
   expect(w.findAll('.tabla-errores tbody tr')).toHaveLength(1)
   expect(w.get('.tabla-errores').text()).toContain('Documento tanda 1')
   await w.findAll('.tabs .tab-btn')[2].trigger('click'); await flushPromises()
   expect(w.findComponent({ name: 'TrazabilidadArticulo' }).props('ambitoInicial')).toBe('HISTORICO')
   w.unmount()
 })
 it('indica que las siguientes fotografías irán a Tanda 2 aunque se consulte Tanda 1', async () => {
   const w=await montar()
   await w.findAll('.tandas-controles button')[1].trigger('click')
   await w.get('.with-action button').trigger('click')
   expect(w.text()).toContain('Subir Fotografías del Kárdex · Tanda 2')
   w.unmount()
 })
 it('el Auditor consulta tandas y no ofrece escanear', async () => {
   auth.rol='Auditor'
   const w=await montar()
   expect(w.findAll('.tandas-controles button')).toHaveLength(3)
   expect(w.find('.with-action button').exists()).toBe(false)
   w.unmount()
 })
})
