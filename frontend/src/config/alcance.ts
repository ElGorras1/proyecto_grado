// Límite documental acordado para el proyecto. No altera fechas de operaciones.
export const GESTION_DOCUMENTAL_HASTA = 2025

export function ultimaGestionDocumental(gestiones: number[]): number | '' {
  const disponibles = gestiones.filter(g => Number.isInteger(g) && g >= 1900 && g <= GESTION_DOCUMENTAL_HASTA)
  return disponibles.length ? Math.max(...disponibles) : ''
}
