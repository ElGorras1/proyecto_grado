# ADR-0001: Separación de movimientos Legacy y transacciones modernas

- **Estado:** Propuesto para aprobación.
- **Fecha:** 2026-09-18.
- **Responsables:** equipo del Sistema de Gestión y Trazabilidad de Activos.

## Contexto

`movimientos_kardex` almacena actualmente dos clases de información con ciclos de vida distintos:

- Filas históricas extraídas desde documentos físicos, sujetas a errores OCR, validación matemática
  y corrección Human-In-The-Loop.
- Operaciones modernas realizadas por usuarios autenticados, que afectan el stock institucional.

La tabla contiene 1.258 filas Legacy y 9 modernas. El stock se obtiene desde el último saldo por
artículo y una anulación reescribe los saldos modernos posteriores. Las tablas `existencia` y
`movimiento` del diseño original todavía están vacías.

El histórico OCR no puede tratarse como transacciones operativas confiables ni alimentar directamente
el modelo de anomalías. A su vez, una corrección documental no debe reescribir el inventario vivo.

## Decisión propuesta

### 1. Mantener una capa de evidencia inmutable

Cada archivo, página y resultado original de extracción conservará su procedencia, checksum, versión
del modelo y fecha de procesamiento. Una corrección nunca sobrescribirá el valor original.

Antes de crear tablas nuevas se evaluará la adaptación de `documento_legacy`, `extraccion_legacy` y
`validacion_legacy`.

### 2. Crear un histórico normalizado independiente

`movimiento_historico` contendrá la interpretación normalizada de una fila Legacy, incluyendo:

- Artículo, fecha y valores normalizados.
- Saldo impreso y saldo calculado.
- Referencia exacta a lote, documento, página y fila.
- Estado de validación.
- Códigos de error y nivel de confianza.
- Versión de la corrección aprobada.

Sus correcciones producirán nuevas revisiones o eventos de validación; no modificarán el ledger
moderno automáticamente.

### 3. Crear un ledger moderno append-only

`transaccion_inventario` almacenará únicamente operaciones digitales confiables:

- Cantidad positiva y tipo que determina la dirección.
- Fecha de operación y fecha de registro.
- Usuario mediante clave foránea.
- Área, contraparte y documento de respaldo.
- Clave de idempotencia.
- Referencia a la transacción original en caso de reversión.

Las transacciones no se eliminarán ni se reescribirán. Una anulación generará una transacción
compensatoria.

### 4. Persistir la existencia actual

`existencia_actual` será la proyección de stock por artículo y ubicación. Registro de transacción,
validación de stock, actualización de existencia y auditoría se confirmarán en una sola transacción
SQL con bloqueo de la fila correspondiente.

Los cierres periódicos se conservarán en `snapshot_existencia`; no serán la fuente primaria del stock
en vivo.

### 5. Establecer un corte explícito

Un `corte_inventario` aprobado definirá fecha, artículo, saldo Legacy aceptado y saldo de apertura del
sistema moderno. Después del corte:

- Una corrección histórica no cambiará silenciosamente el stock moderno.
- Una diferencia requerirá un ajuste moderno autorizado y auditable.
- Los periodos cerrados no admitirán movimientos retroactivos ordinarios.

### 6. Restringir la analítica forense

Isolation Forest consumirá solamente transacciones modernas, validadas y no revertidas. Su salida se
interpretará como una anomalía que requiere investigación, nunca como confirmación automática de
fraude.

Los movimientos legacy distinguirán ausencia documental, área no catalogada y OCR ambiguo. Una
ausencia confirmada se proyectará como `Origen no especificado` o `Destino no especificado`, según la
dirección del movimiento, sin tratar esos nodos virtuales como ubicaciones físicas. Un texto legible
sin equivalencia usará `AREA_NO_CATALOGADA`; un texto ilegible o coincidencia dudosa usará
`PENDIENTE_HIL`. Los dos últimos estados requieren HIL. El texto OCR original y la imagen fuente
permanecerán disponibles para su reclasificación.

## Estrategia de transición

1. Crear tablas nuevas mediante una migración aditiva.
2. Mantener `movimientos_kardex` intacta durante la transición.
3. Clasificar el backfill mediante una regla verificable:
   - `lote_id IS NOT NULL` → histórico.
   - `lote_id IS NULL` → moderno.
4. Ejecutar el backfill de forma idempotente sobre una copia restaurada.
5. Reconciliar conteos, fechas, saldos, artículos y hashes.
6. Cambiar primero las escrituras modernas y después las lecturas.
7. Dejar la tabla anterior en solo lectura durante un periodo de estabilización.
8. Eliminarla únicamente mediante un ADR posterior y un backup verificable.

## Consecuencias positivas

- El OCR deja de contaminar la analítica forense.
- Las correcciones históricas no bloquean ni reescriben el inventario vivo.
- Registrar y revertir una transacción moderna pasa a costo O(1).
- Las constraints y permisos reflejan mejor cada dominio.
- La procedencia documental y la auditoría quedan explícitas.

## Costos y riesgos

- Será necesario mantener temporalmente dos modelos de lectura.
- El backfill debe demostrar reconciliación exacta.
- Habrá que definir un saldo de corte por artículo.
- Los endpoints y el frontend deberán migrarse gradualmente.
- Una doble escritura temporal, si se adopta, aumenta el riesgo de divergencia.

## Decisiones abiertas antes de implementar la migración

1. ¿Cuál será la fecha oficial de corte por artículo?
2. ¿El stock se controlará globalmente o por área/ubicación?
3. ¿Quién puede aprobar correcciones HIL: Operador, Auditor o ambos?
4. ¿Las cantidades continuarán siendo enteras o se admitirán unidades decimales?
5. ¿Qué campos actuales se trasladarán a tablas especializadas y cuáles a metadatos tipados?
6. ¿Se reutilizará `movimiento` o se creará `transaccion_inventario` explícitamente?
7. ¿Se permitirá doble escritura durante el corte o se usará una ventana de mantenimiento?

## Criterio de aprobación

Este ADR puede marcarse como **Aceptado** cuando las decisiones abiertas tengan respuesta institucional,
el diccionario de datos esté revisado y exista un backup restaurable de base de datos y evidencias.
