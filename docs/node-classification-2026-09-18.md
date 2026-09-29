# Clasificación de áreas y referencias legacy — 2026-09-18

## Decisión

La ausencia documental no se mezcla con una clasificación OCR dudosa. `area` y `referencia`
continúan guardando el texto original; los campos `area_estado`, `referencia_estado` y sus banderas
de auditoría guardan la interpretación normalizada.

| Estado de área | Filas | Tratamiento |
|---|---:|---|
| `NO_APLICA` | 756 | Operación reconocida: venta, feria, donación o consignación |
| `RESUELTA_AUTOMATICAMENTE` | 311 | Coincidencia exacta o sinónimo confirmado |
| `SIN_AREA_REGISTRADA` | 164 | Nodo virtual de origen/destino no especificado |
| `AREA_NO_CATALOGADA` | 17 | Revisión HIL para crear área o sinónimo |
| `PENDIENTE_HIL` | 10 | OCR ilegible, ambiguo o coincidencia no confirmada |

| Estado de referencia | Filas |
|---|---:|
| `AUSENTE` | 762 |
| `PRESENTE` | 496 |
| `ILEGIBLE` / `INCIERTA` | 0 |

Total reconciliado: **1,258 movimientos legacy**. La reclasificación modificó el nodo o su bandera
en 324 filas y redujo la cola de clasificación a **27 casos HIL reales**. No se modificaron `area`,
`referencia`, fechas, cantidades, saldos ni rutas de las imágenes fuente.

## Reglas analíticas

- `AREA_NO_CATALOGADA` y `PENDIENTE_HIL` se excluyen de datasets analíticos hasta resolverse.
- `SIN_AREA_REGISTRADA` puede conservarse como categoría y bandera de ausencia confirmada.
- La ausencia de referencia es una característica auditable, no un nodo del grafo.
- Un resultado de Isolation Forest representa una anomalía para investigar, no fraude confirmado.
