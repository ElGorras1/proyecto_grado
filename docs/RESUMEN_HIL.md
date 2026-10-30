# Resumen único de revisión Human in the Loop

**Cola inicial revisada: 18/10/2026; continuidad N01: 28/10/2026, Bolivia.** [Sistema y datos](../README.md) · [Avances y pendientes](AVANCES_Y_PENDIENTES.md).

**Revalidación del 29/10:** las consultas de solo lectura conservan 117 movimientos históricos activos categorizados con marca, cero sin categorizar/recategorizar y 8.367 elegibles. Las 60 decisiones de área siguen distribuidas en 32 asignaciones inferidas, 13 equivalencias, 8 lecturas inciertas, 6 marcas y 1 efecto indeterminado. Las 693 rutas de fotos históricas activas están presentes; esto no supone un nuevo cotejo visual de todas las celdas. No se alteraron decisiones, datos ni exclusiones. La confirmación de cobertura sigue sin registros y la revisión humana analítica continúa en cero, como flujos separados del HIL documental. [Diagnóstico de cierre](../outputs/diagnostico-cierre-20261029/Diagnostico_para_terminar_el_sistema.md).

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

## Categorías de los 116 casos iniciales

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

El seguimiento automático anterior sigue eliminado y la importación no se reactiva. La consolidación del 18/10 no autorizaba por sí sola nuevos entrenamientos ni operaciones. El titular dio posteriormente la instrucción explícita de entrenar el 20/10.

La auditoría integral posterior del 18/10 comprobó nuevamente las huellas y los 116 tratamientos categorizados: no modificó movimientos ni reabrió el cotejo. Corrigió los contadores del catálogo para excluir notas/anulaciones y mantener el mismo alcance que la bandeja HIL. La cadena completa de revisiones previas continúa almacenada y auditable, aunque ya no se repite en cada fila de los listados. El diagnóstico y sus pruebas se resumen en [el README](../README.md#auditoría-integral-del-18102026).

El entrenamiento histórico autorizado del 20/10 creó la versión retrospectiva `46e3683e-0210-4917-aadf-656af9dd2e2c` con 8.367 candidatos elegibles, separados en entrenamiento, calibración y evaluación. Los 116 movimientos con marca y los 40 artículos excluidos conservan sus decisiones y restricciones; no se corrigieron cifras, fechas, fotos ni observaciones durante ese entrenamiento. Los resultados analíticos nuevos requieren su propia revisión humana y no constituyen una nueva validación HIL. El [resultado técnico](../backend/backups/entrenamiento_historico_20261020/resultado.json) documenta las comprobaciones.

## Continuidad N01, 28/10/2026

Por la instrucción posterior de completar las tareas de continuidad una por una, N01 incorpora representación explícita de fechas ausentes, parciales e ilegibles. Se cotejó la fotografía del movimiento 12272: el primer ingreso tiene FECHA vacía. La fecha técnica `2023-01-01` se conserva en la primera lectura y en la revisión anterior; la fecha vigente queda `null`, con precisión AUSENTE y estado SIN_FECHA_DOCUMENTAL. No se cambiaron cantidades, saldo ni originales, ni se reabrió el cotejo general.

El caso tiene tratamiento **Dato ausente en el documento**, con criterio T09/N01, motivo y huella de su evidencia. Se conserva fuera del entrenamiento y de las gestiones anuales. Esto añade una fila a las 116 marcas anteriores: **400 casos tratados en total, 283 sin avisos, 117 con marca y cero sin categorizar**. Son 118 decisiones en 117 filas por el solapamiento inicial ya documentado. Las categorías y huellas anteriores siguen vigentes.

La asistencia de Codex y la constatación de una celda vacía no se atribuyen a un funcionario institucional ni confirman el día del hecho. La aprobación institucional y la evaluación del detector siguen pendientes. [Evidencia y aplicación de N01](../backend/backups/n01_fechas_20261028/cambio_focalizado.json).

## Continuidad de áreas históricas por instrucción posterior, 28/10/2026

El titular indicó asignar por parecido, frecuencia y correlaciones y confirmó que **C+C era un área antigua de la institución, actualmente cerrada**. Esta instrucción posterior autoriza una clasificación inferida por fila; no acredita las expansiones institucionales desconocidas de otras siglas. Se conserva la lectura literal y se distingue la inferencia de una corrección fotográfica o una identidad confirmada.

Se asignaron 32 movimientos a Capacitación (19), C+C (4), Galería (3), CEDOAL (3), CID (2) y Sala (1), con literal, regla, frecuencias de apoyo, alternativas, soporte y huella del plan. Se mantiene `PENDIENTE_HIL`, la exclusión analítica y la nueva categoría **Área asignada por correlación**. Los niveles ALTO/MEDIO son soporte heurístico, no probabilidades medidas. CEDOC y CEDOAL siguen separados; C+C conserva su estado inactivo y no se usa como área operativa activa.

La distribución vigente de las 60 marcas de área es: 32 asignaciones inferidas, 13 equivalencias sin confirmar, 8 lecturas inciertas, 6 marcas del papel y 1 efecto indeterminado. Las otras categorías de la cola siguen vigentes. No aumentó ni disminuyó el total de 117 movimientos con marca/118 decisiones; no hay casos sin categorizar o que requieran recategorizar. Las 32 decisiones de área previas permanecen en las auditorías, junto a sus nuevos valores.

Hay respaldo restaurado, ensayo previo y 32 auditorías nuevas. Se verificaron todas las filas ajenas, las fuentes, cantidades, fechas y saldos, catálogos, alias y los 927 archivos privados sin cambios. Los 8.367 elegibles y el modelo entrenado permanecen intactos y consistentes. El HIL y el grafo muestran el área inferida y la sigla conservada. Una edición de otro campo no confirma automáticamente el nodo; una decisión manual expresa posterior lo conserva como inferencia sustituida.

La aplicación del 28/10 no declara terminada la confirmación institucional de áreas ni corrigió los siete nodos «Área: Ventas». Estos últimos se corrigieron después en C01, según el apartado siguiente. [Casos aplicados y restantes](../outputs/revision-areas-historicas-20261028/Asignacion_areas_historicas.md) y [comprobación posterior](../backend/backups/revision_areas_historicas_20261028/verificacion_asignacion.json).

## C02: fuente de cierre y validación pendiente, 29/10/2026

Se implementó la selección explícita de fila y fotografía de cierre con referencia, motivo, responsable y huella. Las decisiones desactualizadas se rechazan; las aperturas ya utilizadas se conservan. El flujo tiene controles y pruebas técnicas, pero no confirma automáticamente el archivo: permanecen 397 propuestas y cero confirmaciones documentales. Se mantienen 117 tratamientos con marca, 8.367 elegibles y dos modelos consistentes. [Detalle de C02](../outputs/cierre-documental-20261029/Cierre_documental_C02.md).

## C03: administración de equivalencias, 29/10/2026

Se implementó la administración de áreas, catálogo documental, alias y adscripción de cuentas con historial. Desactivar un alias impide nuevas asignaciones automáticas por esa lectura. Confirmarlo requiere cotejo explícito y motivo, y no confirma retrospectivamente las filas existentes. Permanecen 32 inferencias, otros 28 avisos de área, 117 marcas y 8.367 elegibles. C+C sigue histórica/inactiva. [Detalle de C03](../outputs/areas-catalogos-20261029/Administracion_areas_C03.md).

## C01: corrección técnica del tipo de catálogo, 29/10/2026

Por instrucción del titular de completar una tarea por vez se corrigieron siete nodos «Área: Ventas» a «Salida: Ventas», con estado `NO_APLICA`. Los siete movimientos estaban sin avisos HIL; siguen así. Se conservaron la columna AREA escrita, los originales y todas las decisiones documentales. La corrección es de clasificación técnica, no una nueva transcripción ni una confirmación atribuida a personal institucional.

El clasificador distingue departamentos y operaciones en coincidencias exactas, alias y sugerencias, conservando las propuestas no confirmadas con HIL. Hubo respaldo restaurado, ensayo, siete auditorías y reconciliación de las demás filas/tablas. Permanecen 117 tratamientos con marca, 60 decisiones de área (incluidas las 32 inferidas) y los mismos 8.367 elegibles. Los modelos congelados siguen consistentes; cuatro filas elegibles tienen una clasificación vigente corregida para un corte posterior. No se reentrenó ni se registraron etiquetas analíticas. [Verificación de C01](../backend/backups/c01_operaciones_catalogo_20261029/verificacion.json).

El cuaderno de calibración experimental preparado y ejecutado el 28/10 usa las variables y particiones congeladas del modelo del 20/10. No vuelve a incorporar las áreas inferidas ni modifica decisiones HIL o etiquetas humanas. Mantiene 0 etiquetas en el material de análisis y presenta precisión, recall, F1 y ROC-AUC como pendientes de Ground Truth independiente. Sus experimentos de umbral/árboles son diagnósticos locales; no activan versiones nuevas. [Informe de calibración](../outputs/calibracion-isolation-forest-20261028/Calibracion_Isolation_Forest.html).
