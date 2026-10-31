import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ValidacionProyectoView from './ValidacionProyectoView.vue'
const { get, post, auth } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), auth: { rol: 'Auditor' } }))
vi.mock('@/services/api', () => ({ default: { get, post, defaults: { baseURL: 'http://qa.test/api/v1' } } }))
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }))
const cabecera = { version: 2, id: 8, tipo: 'DETECTOR', creada_en: '2026-10-29T14:00:00Z', creada_por: 1,
  modelo_id: 'modelo-qa', semilla: 'qa', referencia_protocolo: 'PROTOCOLO-QA de revisión',
  huella_estudio: 'a'.repeat(64), poblacion: 1615, seleccionadas: 2, alcance: 'Resultados solo de la muestra.' }
function detalle() { return { ...cabecera, puede_etiquetar: true, filas: [1, 2].map(id => ({ id, evidencia_vigente: true,
  documento: { articulo: 'Libro de prueba', codigo: 'QA-8', lote_id: 5, numero_pagina: 1, orden_fila: id,
    fecha: null, fecha_documental_texto: 'mayo de 2008', detalle: 'Salida registrada en el documento',
    referencia: null, area: 'Galería', ingresos: null, salidas: 2, saldo_registrado: 18,
    ruta_imagen_respaldo: 'storage/kardex_images/qa.png' }, revision: null })) } }
function reporte() { return { ...cabecera, estado: 'PENDIENTE',
  progreso: { seleccionadas: 2, etiquetadas: 0, concluyentes: 0, pendientes: 2,
    evidencias_no_vigentes: 0, modelo_consistente: true },
  metricas: { concordancia_filas: null, precision: null, recall: null, f1: null, matriz: null } } }
beforeEach(() => {
  vi.clearAllMocks(); auth.rol = 'Auditor'
  get.mockImplementation((url: string) => Promise.resolve({ data: url === '/validacion/estudios' ? { total: 1, filas: [cabecera] }
    : url === '/validacion/marco' ? { poblacion: 400, tamano_documental_sugerido: 197, filtros: 'Marco técnico pendiente de cotejo.' } : url === '/analitica/modelos' ? { filas: [] } : url.endsWith('/informe.json') ? reporte() : detalle() }))
  post.mockResolvedValue({ data: { id: 9, usuario_id: 2, fecha: cabecera.creada_en,
    etiqueta: 'NORMAL', motivo: 'Cotejo documentado en QA', referencia: 'ACTA-QA' } })
})
async function montar() {
  const w = mount(ValidacionProyectoView, { global: { stubs: { RouterLink: RouterLinkStub } } })
  await flushPromises()
  await w.get('[aria-label="Estudios guardados"]').findAll('button').find(b => b.text().startsWith('#8'))!.trigger('click')
  await flushPromises(); return w
}
describe('Validación del proyecto', () => {
  it('ofrece el marco recalculado y clases documentales nuevas sin seleccionar una respuesta', async () => {
    const w = await montar()
    const formulario = w.get('[aria-label="Preparar estudio"]')
    expect(formulario.get<HTMLInputElement>('input[type="number"]').element.value).toBe('197')
    expect(formulario.get('input[type="number"]').attributes('max')).toBe('400')
    const opciones = w.get('[aria-label="Conclusión"]').findAll('option').map(o => o.attributes('value'))
    expect(opciones).toEqual(['', 'NORMAL', 'ANOMALO', 'INDETERMINADO'])
    expect(w.get<HTMLSelectElement>('[aria-label="Conclusión"]').element.value).toBe('')
    w.unmount()
  })
  it('exige identificar la inconsistencia antes de registrar una anomalía', async () => {
    const w = await montar(), form = w.get('[aria-label="Registrar conclusión"]')
    await form.get('[aria-label="Conclusión"]').setValue('ANOMALO')
    await form.get('textarea').setValue('Se verificó la inconsistencia en cantidades con el acta.')
    await form.get('input[type="text"]').setValue('ACTA-QA')
    await form.get('input[type="checkbox"]').setValue(true)
    expect(form.get('button').attributes('disabled')).toBeDefined()
    await form.get('[aria-label="Criterio de anomalía"]').setValue('CANTIDAD')
    await form.trigger('submit'); await flushPromises()
    expect(post).toHaveBeenCalledWith('/validacion/estudios/8/filas/1/etiqueta', expect.objectContaining({ etiqueta: 'ANOMALO', criterio: 'CANTIDAD', segunda_revision: false }))
    w.unmount()
  })
  it('registra explícitamente el segundo cotejo sin asumirlo por una etiqueta indeterminada', async () => {
    const datos = detalle();datos.filas[0].revision = { id: 22, usuario_id: 2, fecha: cabecera.creada_en,
      etiqueta: 'INDETERMINADO', motivo: 'Respaldo insuficiente en primer cotejo.', referencia: 'ACTA-QA' } as any
    get.mockImplementation((url: string) => Promise.resolve({ data: url === '/validacion/estudios' ? { total: 1, filas: [cabecera] }
      : url === '/validacion/marco' ? { poblacion: 400, filtros: 'Marco técnico' } : url === '/analitica/modelos' ? { filas: [] } : datos }))
    const w = await montar(), form = w.get('[aria-label="Registrar conclusión"]')
    expect(form.get<HTMLInputElement>('[aria-label="Segunda revisión"]').element.checked).toBe(false)
    await form.get('[aria-label="Conclusión"]').setValue('INDETERMINADO')
    await form.get('textarea').setValue('El segundo cotejo no pudo resolver la falta de respaldo.')
    await form.get('input[type="text"]').setValue('SEGUNDO-COTEJO-QA')
    await form.get('input[type="checkbox"]').setValue(true)
    await form.get('[aria-label="Segunda revisión"]').setValue(true)
    await form.trigger('submit'); await flushPromises()
    expect(post).toHaveBeenCalledWith('/validacion/estudios/8/filas/1/etiqueta', expect.objectContaining({ etiqueta: 'INDETERMINADO', segunda_revision: true, revision_esperada: 22 }))
    w.unmount()
  })
  it('conserva los criterios anteriores de un estudio antiguo sin convertir sus clases', async () => {
    get.mockImplementation((url: string) => Promise.resolve({ data: url === '/validacion/estudios' ? { total: 1, filas: [cabecera] }
      : url === '/validacion/marco' ? { poblacion: 400, filtros: 'Marco técnico' } : url === '/analitica/modelos' ? { filas: [] } : { ...detalle(), version: 1 } }))
    const w = await montar()
    expect(w.get('[aria-label="Conclusión"]').findAll('option').map(o => o.attributes('value'))).toContain('INUSUAL_RELEVANTE')
    expect(w.text()).toContain('conserva los criterios anteriores')
    expect(w.find('[aria-label="Criterio de anomalía"]').exists()).toBe(false)
    w.unmount()
  })
  it('no preselecciona una conclusión ni muestra datos del predictor y no inventa métricas', async () => {
    const w = await montar()
    expect(w.get<HTMLSelectElement>('[aria-label="Registrar conclusión"] select').element.value).toBe('')
    expect(w.text()).toContain('mayo de 2008')
    expect(w.find('[aria-label="Revisión independiente"] .score').exists()).toBe(false)
    await w.findAll('button').find(b => b.text() === 'Consultar métricas')!.trigger('click'); await flushPromises()
    const panel = w.get('[aria-label="Métricas de la muestra"]')
    expect(panel.text()).toContain('Pendiente / no definida')
    expect(panel.text()).not.toContain('0.0%')
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('guarda una conclusión explícita con versión y declaración, y limpia antes de la siguiente fila', async () => {
    const w = await montar(), form = w.get('[aria-label="Registrar conclusión"]')
    await form.get('select').setValue('NORMAL')
    await form.get('textarea').setValue('Cotejé documento y referencia del archivo.')
    await form.get('input[type="text"]').setValue('ACTA-QA')
    expect(form.get('button').attributes('disabled')).toBeDefined()
    await form.get('input[type="checkbox"]').setValue(true)
    await form.trigger('submit'); await flushPromises()
    expect(post).toHaveBeenCalledWith('/validacion/estudios/8/filas/1/etiqueta', expect.objectContaining({
      etiqueta: 'NORMAL', independiente: true, revision_esperada: 0, huella_estudio: 'a'.repeat(64) }))
    await w.findAll('button').find(b => b.text() === 'Fila siguiente')!.trigger('click')
    expect(form.get<HTMLSelectElement>('select').element.value).toBe('')
    expect(form.get<HTMLTextAreaElement>('textarea').element.value).toBe('')
    w.unmount()
  })
  it('muestra la matriz solo cuando el informe ofrece conclusiones completas', async () => {
    const w = await montar()
    get.mockResolvedValueOnce({ data: { ...reporte(), estado: 'MUESTRA_COMPLETA',
      progreso: { ...reporte().progreso, concluyentes: 2, pendientes: 0 },
      metricas: { concordancia_filas: null, precision: .5, recall: 1, f1: 2/3, matriz: { tp: 1, fp: 1, fn: 0, tn: 0 } } } })
    await w.findAll('button').find(b => b.text() === 'Consultar métricas')!.trigger('click'); await flushPromises()
    expect(w.get('[aria-label="Métricas de la muestra"]').text()).toContain('66.7%')
    expect(w.get('caption').text()).toContain('positivo = anomalía documental verificada')
    w.unmount()
  })
  it('mantiene consulta sin formulario para Operador y quien no puede etiquetar', async () => {
    auth.rol = 'Operador'
    get.mockImplementation((url: string) => Promise.resolve({ data: url === '/validacion/estudios' ? { total: 1, filas: [cabecera] }
      : { ...detalle(), puede_etiquetar: false } }))
    const w = await montar()
    expect(w.find('[aria-label="Preparar estudio"]').exists()).toBe(false)
    expect(w.find('[aria-label="Registrar conclusión"]').exists()).toBe(false)
    expect(w.text()).toContain('distinta de quien lo preparó')
    expect(post).not.toHaveBeenCalled()
    w.unmount()
  })
  it('conserva el motivo y comunica un conflicto de revisión sin reintento automático', async () => {
    const w = await montar(), form = w.get('[aria-label="Registrar conclusión"]')
    post.mockRejectedValueOnce({ response: { data: { detail: 'La fila ya fue revisada; actualiza antes de guardar.' } } })
    await form.get('select').setValue('NORMAL'); await form.get('textarea').setValue('Cotejo con el archivo institucional.')
    await form.get('input[type="text"]').setValue('ACTA-QA'); await form.get('input[type="checkbox"]').setValue(true)
    await form.trigger('submit'); await flushPromises()
    expect(w.get('[role="alert"]').text()).toContain('actualiza')
    expect(form.get<HTMLTextAreaElement>('textarea').element.value).toContain('Cotejo')
    expect(post).toHaveBeenCalledTimes(1)
    w.unmount()
  })
})
