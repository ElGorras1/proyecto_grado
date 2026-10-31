import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, expect, it, vi } from 'vitest'
import DocumentosOperativos from './DocumentosOperativos.vue'
import api from '@/services/api'
vi.mock('@/services/api', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
beforeEach(() => { vi.resetAllMocks(); vi.mocked(api.get).mockResolvedValue({ data: [] }) })
it('permite consultar sin ofrecer carga al auditor', async () => {
  const w = mount(DocumentosOperativos, { props: { articuloId: 7, puedeSubir: false } })
  await flushPromises()
  expect(api.get).toHaveBeenCalledWith('/kardex/articulos/7/documentos')
  expect(w.find('form').exists()).toBe(false)
  expect(w.text()).toContain('Sin documentos adjuntos')
  w.unmount()
})
it('presenta documentos y permite carga a los roles autorizados', async () => {
  vi.mocked(api.get).mockResolvedValue({ data: [{ id: 1, nombre: 'Acta.pdf', referencia: 'ACTA-01' }] })
  const w = mount(DocumentosOperativos, { props: { articuloId: 7, puedeSubir: true } })
  await flushPromises()
  expect(w.text()).toContain('ACTA-01')
  expect(w.find('input[type="file"]').exists()).toBe(true)
  w.unmount()
})
