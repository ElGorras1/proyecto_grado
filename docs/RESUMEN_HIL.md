# Resumen único de revisión Human in the Loop

**Estado: 18/10/2026, Bolivia.** [Sistema y datos](../README.md) · [Avances y pendientes](AVANCES_Y_PENDIENTES.md).

Este documento sustituye los informes narrativos por lote. La fotografía, primera extracción, dato vigente y auditoría de cada caso permanecen en sus fuentes; no se eliminan porque se reduzca la documentación.

## Resultado y alcance

La instrucción vigente fue revisar **solo los movimientos observados en el HIL**. Las filas vecinas se consultaron como contexto, sin continuar el cotejo masivo del histórico.

| Resultado de la cola inicial | Movimientos |
|---|---:|
| Total observado tratado | 399 |
| Sin avisos HIL tras correcciones | 283 |
| Categorizados con marca conservada | 116 |
| Sin categorizar | **0** |

El cierre del 16/10 había dejado 155 sin avisos y 244 pendientes documentados. La reanudación del 18/10 resolvió **128 avisos adicionales** mediante planes 86–88 y 90–94. El plan 95 registró el tratamiento explícito de los 116 restantes; no los convirtió en datos confirmados.

Se corrigieron lecturas de textos y unidades acreditadas, se separaron referencias geográficas y documentales de áreas institucionales y se conservaron interpretaciones y posiciones escritas. Para la categorización final se reutilizó el cotejo previo y se verificaron las huellas de sus 94 fotografías; no se simuló una nueva revisión completa de cada hoja.

## Criterios acordados

Resumen operativo de las 23 respuestas del titular, conservadas íntegramente en la [política congelada](../backend/backups/aplicacion_hil_20261014/criterios_version_1.json):

| Criterio | Tratamiento |
|---|---|
| T01 | Corregir cifras mal leídas; lo tapado o no acreditado permanece hipotético. |
| T02 | Corregir entradas y salidas intercambiadas por OCR según la evidencia. |
| T03 | Distinguir paréntesis o anotaciones de una segunda operación; conservar la interpretación. |
| T04 | Resolver desplazamientos y anotaciones con contexto, registrando las discrepancias del papel. |
| T05 | Mantener saldo escrito y cálculo independiente cuando el error aritmético persiste. |
| T06 | Corregir errores de lectura que parecían compensarse, según la foto y confirmaciones. |
| T07 | Interpretar una columna equivocada del trabajador con evidencia, preservando su posición original. |
| T08 | Representar saldos en blanco mediante cálculo identificado; blanco no equivale a cero escrito. |
| T09 | Identificar fecha ausente o parcial; una fecha técnica de consulta no acredita el día del hecho. |
| T10–T11 | Conservar fecha documental y marcar ajustes de secuencia; no fabricar certeza cronológica. |
| T12 | Corregir el orden documental de hojas con evidencia, preservando fotos y numeración de origen. |
| T13 | Aplicar la aclaración humana a sus cuatro ingresos; no extenderla automáticamente a otros cuadros. |
| T14 | Distinguir celda tachada de fila anulada; conservar ambas evidencias. |
| T15 | Reconocer un recuento físico expresamente escrito como nueva base, documentando su diferencia. |
| T16 | Interpretar notas marginales y ejemplares dañados con evidencia y motivo. |
| T17 | Separar unidad, receptor, lugar y referencia; no unir instituciones por mera frecuencia o parecido. |
| T18 | Repetir la misma columna ante comillas inequívocas; un punto aislado queda como marca incierta. |
| T19 | Conservar incertidumbre de datos tapados, recortados o ilegibles y las hipótesis usadas. |
| T20 | Respetar la agrupación de hojas confirmada al escanear aunque los títulos varíen. |
| T21 | No eliminar renglones parecidos sin prueba de duplicación; conservar observación y exclusión. |
| T22 | Distinguir base documental de ingreso y mantener el origen de una base inferida. |
| T23 | Recuperar cantidades omitidas o mal ubicadas desde la evidencia, sin inventar operaciones. |

Siempre se conservan **fuente original, dato vigente y decisión de revisión**. La asistencia de Codex no se registra como aprobación de un funcionario institucional.

## Categorías de los 116 casos

| Categoría | Marcas |
|---|---:|
| Discrepancia del documento | 26 |
| Ámbito de la hoja no confirmado | 5 |
| Dependencia de otra fila | 7 |
| Nombre o sigla sin equivalencia confirmada | 36 |
| Lectura no inequívoca | 21 |
| Marca del papel conservada | 20 |
| Efecto del movimiento no acreditado | 1 |
| Operaciones parecidas conservadas | 1 |

Son **117 decisiones en 116 filas**: una tiene marca de área y de referencia. Por tipo original permanecen 34 avisos de saldo, 5 de fecha, 60 de área y 18 de referencia, también solapados en esa fila.

«Categorizado» significa que el problema tiene tratamiento explícito. No significa que la sigla ya identifique una unidad, que una fecha sea cierta o que el saldo escrito sea correcto. Las diferencias e incertidumbres reales siguen visibles y estos 116 movimientos siguen excluidos de la selección analítica.

## Qué se ve en la pantalla

En **Kárdex escaneados → artículo → Auditoría HIL** se puede filtrar por tipo, tanda, tratamiento y categoría. **Revisión documental** muestra decisión, criterio y explicación junto a sus valores y evidencia. El historial conserva las revisiones previas.

Cada tratamiento tiene una huella de los datos revisados. Un cambio posterior relevante lo muestra como **Revisar categoría tras cambios**, conservando la decisión anterior sin presentarla como vigente.

Corregir OCR modifica la lectura vigente con auditoría. Una discrepancia auténtica del papel permanece como hallazgo y se compara con el cálculo independiente. Una hipótesis conserva su marca y exclusión; no se presenta como certeza para obtener cero avisos.

## Decisiones que no deben revertirse

- **Campero:** cierre escrito 300 y cálculo condicional 309, con exclusión y apertura bloqueada; no crear ajustes para hacerlos coincidir.
- **POLIGENESIS** y **REV DE HISTORIA POLIGENESIS 1:** artículos separados por decisión del titular, aunque compartan fotografías.
- **T13 confirmado:** cuatro ingresos 1, 2, 1 y 4, sin reinterpretarlos como notas por su apariencia.
- **Cifras tapadas o fechas técnicas:** mantener origen hipotético o secuencia ajustada; no completar información por frecuencia.
- **Errores de saldo, recuentos y discontinuidades:** conservar las diferencias y protecciones de cada artículo; no fabricar ventas o recepciones compensatorias.
- **Dependencias de vecinos normales:** registrar la relación sin ampliar los objetivos ni modificar esos vecinos durante esta revisión.

## Comprobación y cierre de esta revisión

Hubo planes congelados, respaldo coherente, ensayo en copia restaurada y aplicación secuencial. En el plan 95 se añadieron decisiones y 116 auditorías, conservando exactamente los demás campos de los objetivos. No se alteraron filas normales, originales, fotos, cantidades, fechas, áreas, referencias ni saldos.

Se verificaron las categorías vigentes y filtros, las consultas de historial sin escrituras, las exclusiones y la ausencia de duplicaciones. El cambio registró **32 pruebas backend y 13 frontend aprobadas**, más compilación correcta. No se ejecutó un nuevo entrenamiento.

La revisión asistida de la cola acordada queda cubierta. Nuevas evidencias pueden resolver categorías inciertas; no corresponde repetir toda la revisión ni declarar confirmados todos los datos para pasar al siguiente módulo.

Para recuperación técnica se conserva el [resultado verificable de los 116 tratamientos](../backend/backups/revision_avisos_hil_20261018/clasificacion_116_verificada.json), la [cola y estado focalizados](../backend/backups/revision_avisos_hil_20261016/estado_avisos.json) y los planes en `backend/backups/aplicacion_hil_20261014/`. Los planes 48, 58, 65, 67, 81 y 89 fueron archivados sin aplicación: no ejecutarlos. Los planes aplicados tampoco se reejecutan para reconstruir informes.

El seguimiento automático anterior sigue eliminado y la importación no se reactiva. El siguiente trabajo de entrenamiento, áreas u operación requiere su propia instrucción; esta consolidación solo reduce documentos y conserva evidencia.
