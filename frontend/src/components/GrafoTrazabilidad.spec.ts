import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import GrafoTrazabilidad from '@/components/GrafoTrazabilidad.vue'

// jsdom no implementa un contexto de canvas 2D real, y Cytoscape lo
// necesita para renderizar. En pruebas unitarias no probamos el
// renderizado gráfico en sí (eso se valida visualmente/manualmente),
// sino que el componente se monta y recibe los datos correctamente.
vi.mock('cytoscape', () => ({
  default: vi.fn(() => ({
    destroy: vi.fn(),
  })),
}))

describe('GrafoTrazabilidad', () => {
  it('se monta y crea el contenedor del grafo', () => {
    const wrapper = mount(GrafoTrazabilidad, {
      props: {
        elementos: [
          { data: { id: 'a1', label: 'Activo 1' } },
          { data: { id: 'a2', label: 'Activo 2' } },
          { data: { id: 'e1', source: 'a1', target: 'a2' } },
        ],
      },
    })
    expect(wrapper.find('.grafo-container').exists()).toBe(true)
  })
})
