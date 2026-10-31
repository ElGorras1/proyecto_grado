export const espacios = [
  { ruta: 'articulosInventario', icono: 'pi-box', titulo: 'Artículos e inventario', descripcion: 'Consultar artículos, fotografías, Kárdex y operaciones.', categoria: 'Consultar y registrar' },
  { ruta: 'revisiones', icono: 'pi-check-square', titulo: 'Revisiones y alertas', descripcion: 'Ver qué requiere revisión y abrir su evidencia.', categoria: 'Revisar pendientes' },
  { ruta: 'reportes', icono: 'pi-chart-bar', titulo: 'Reportes', descripcion: 'Movimientos, resúmenes y balances en un solo lugar.', categoria: 'Consultar y descargar' },
  { ruta: 'administracion', icono: 'pi-cog', titulo: 'Administración', descripcion: 'Usuarios, áreas y herramientas de mantenimiento.', categoria: 'Administrar', roles: ['Administrador', 'Auditor'] },
]

export const secciones: Record<string, { ruta: string; titulo: string }[]> = {
  articulosInventario: [{ ruta: 'kardexDigital', titulo: 'Artículos y Kárdex' }, { ruta: 'inventarioVivo', titulo: 'Operaciones de inventario' }],
  revisiones: [{ ruta: 'revisiones', titulo: 'Pendientes' }, { ruta: 'analitica', titulo: 'Consulta del análisis histórico' }, { ruta: 'alertasInventario', titulo: 'Seguimiento operativo' }],
  reportes: [{ ruta: 'reporteInventario', titulo: 'Movimientos' }, { ruta: 'gestionInstitucional', titulo: 'Resumen' }, { ruta: 'cierresGestion', titulo: 'Balance y cierre de gestión' }],
  administracion: [{ ruta: 'administracion', titulo: 'Administración' }, { ruta: 'areasCatalogos', titulo: 'Áreas y equivalencias' }],
}

export function espacioDe(ruta: unknown) {
  if (['kardexDigital', 'inventarioVivo', 'preparacionInventario', 'articulosInventario'].includes(String(ruta))) return 'articulosInventario'
  if (['revisiones', 'analitica', 'alertasInventario'].includes(String(ruta))) return 'revisiones'
  if (['reportes', 'reporteInventario', 'gestionInstitucional', 'cierresGestion'].includes(String(ruta))) return 'reportes'
  if (['administracion', 'usuarios', 'areasCatalogos', 'reporteAccesos', 'validacionProyecto', 'analiticaOperativa', 'mantenimientoAnalitico', 'muestraValidacion'].includes(String(ruta))) return 'administracion'
  return ''
}
