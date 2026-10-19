# Avances y pendientes del proyecto

**Corte documental: 18/10/2026, Bolivia.** [Funcionamiento y datos actuales](../README.md) · [Resumen del HIL](RESUMEN_HIL.md).

Este resumen sustituye los informes narrativos de avance anteriores. Conserva lo vigente y las limitaciones conocidas; una propuesta no se considera implementada por aparecer en este documento.

## Avance conseguido

| Bloque | Resultado |
|---|---|
| Digitalización | Tres tandas incorporadas, fotos y procedencia conservadas, controles de páginas/títulos y reintentos idempotentes. |
| Calidad documental | Aplicación de los criterios del titular. Cola HIL de 399 tratada: 283 sin avisos y 116 categorizados con marca; cero avisos sin categorizar. |
| Inventario y operación | Base histórica separada del stock operativo, entradas/salidas con participantes, áreas, transferencias, devoluciones, custodia y ajustes documentados. |
| Auditoría y reportes | Reglas para histórico y operación digital, casos de seguimiento, libro por artículo, CSV, filtros por gestión, grafo, informe y cierres. |
| Analítica | Módulos histórico y operativo implementados; evaluación y versiones disponibles. No se entrenó una versión nueva con el corte HIL actual. |
| Seguridad y recuperación | Tres roles, evidencias privadas, auditoría y herramientas de respaldo, restauración y piloto aislado. |
| Documentación | Consolidación en tres documentos; informes detallados anteriores archivados con huellas verificadas. |

Las **29 tareas internas anteriores** corresponden a implementación. Se agrupan en apertura/cobertura/HIL, operaciones y stock por área, libro/grafo/custodia, controles y modelos, reportes/cierres y seguridad/recuperación/piloto. No son la misma numeración del cronograma académico ni una declaración de que toda validación institucional esté terminada.

## Qué puede presentarse de las tareas académicas

| Tarea | Avance demostrable | Condición todavía relevante |
|---:|---|---|
| 9 | Reportes de inventario y filtros/descarga por gestión. | Explicar período consultado frente al saldo actual. |
| 10 | Muestras, fotos, decisiones HIL, correcciones y categorías. | La revisión asistida de avisos no sustituye una muestra de investigación validada institucionalmente. |
| 11 | Entradas/salidas con encargado y usuario registrador. | Preparar conteos, participantes y evidencia de uso real. |
| 12 | Transferencias entre áreas implementadas. | Requieren dos áreas autorizadas y existencias ubicadas; una pantalla vacía no demuestra ausencia de la función. |
| 13 | Extracción, normalización, validación, procedencia y correcciones del ETL. | Medir exactitud contra transcripciones verificadas; conservar incertidumbres. |
| 14 | Generación del Kárdex digital por artículo y CSV. | Contrastar apertura, eventos y saldos de un caso del piloto. |
| 15 | Reglas determinísticas para operación y auditoría histórica. | Justificar parámetros y mostrar bloqueos/avisos con evidencia. |
| 16 | Escalamiento de la importación a tres tandas con recuperación y huellas. | Certificar cobertura del archivo y medir tiempos; la pausa de 120 segundos no es tiempo de OCR. |
| 17 | Reportes de movimientos y libro digital. | Verificar cobertura consolidada de transferencias y custodia en la entrega final. |
| 18 | Histórico como base, corte operativo y nuevos eventos con fuentes. | Demostrar un circuito real conciliado, no solo datos ficticios de prueba. |
| 19 | Datos y exportes disponibles; perfil actual reproducible. | Publicar una nueva versión del dataset oficial con diccionario, exclusiones y aprobación. |

La formulación respaldada es «implementado y comprobado técnicamente» cuando existen esas pruebas. «Validado por la institución», «archivo completo» o «precisión del modelo» requieren su evidencia específica.

## Preparación de Isolation Forest

La consulta del 18/10, de solo lectura, selecciona **8.367 movimientos de 356 artículos entre 2005 y 2025**, sin avisos HIL entre los elegibles. Son candidatos previos a la partición, no 8.367 filas necesariamente destinadas a ajustar el bosque.

El módulo histórico ya utiliza cantidad, comparación con referencias, desviación robusta, rareza de nodo y artículo/nodo, ausencia documental de nodo y dirección del movimiento. Las referencias estadísticas se calculan con entrenamiento. Existen modalidades retrospectiva y temporal, con separación y controles de lotes.

El siguiente ciclo debe producir:

1. Dataset versionado, selección y exclusiones explícitas, diccionario y huellas.
2. Particiones verificadas de entrenamiento, calibración y evaluación; comprobar el tamaño efectivo después de agrupaciones o purgas.
3. Nueva versión entrenada con configuración, semilla, archivos y métricas reproducibles.
4. Evaluación humana de alertas y muestra de control; medir utilidad y ajustar el umbral con evidencia.
5. Informe de resultados y decisión sobre uso. El modelo histórico no pasa automáticamente a ser el modelo de operaciones digitales de 2026.

La categorización HIL no habilita los 116 casos marcados ni los artículos excluidos. Modelos antiguos conservan su corte original; esta documentación no los actualiza ni ejecuta entrenamiento.

## Plan de continuidad resumido

Se conservan los identificadores N01–N36 del plan anterior para no perder referencias. Los trabajos no revalidados en este corte mantienen su condición pendiente o de comprobación; no se presume que sigan idénticos todos los hallazgos del 13/10.

| IDs | Trabajo pendiente o condición de cierre |
|---|---|
| N01 | Completar incertidumbre de fechas en extracción y esquema: fecha ausente, parcial y técnica sin presentarla como exacta. |
| N02–N03 | Confirmar la fuente de cierre por artículo y certificar cobertura del archivo/catálogo con evidencia. |
| N04 | Revisión asistida de la cola HIL acordada completada; conservar marcas y resolver nuevas evidencias sin repetir cotejos masivos. |
| N05–N06 | Muestra documental de investigación y publicación del dataset oficial completo y reproducible. |
| N07–N08 | Formalizar/evaluar el grafo y preparar etiquetado independiente para medir resultados de Isolation Forest. |
| N09–N10 | Nueva versión histórica y diseño viable de evaluación temporal, con particiones suficientes e independientes. |
| N11–N12 | Administración y confirmación de áreas/catálogos, participantes, permisos y ámbito operativo. |
| N13–N14 | Conteo y conciliación reales de 2026; adjuntar actas y documentos de negocio. |
| N15 | Simplificar flujos y estados para el personal; el HIL ya distingue categorías y vigencia. |
| N16–N17 | Completar y comprobar rectificaciones específicas de transferencias y de custodia. |
| N18 | Préstamo a exposición con retorno/plazo si la institución confirma ese uso. |
| N19–N20 | Calibración de reglas, patrones acumulados y revisión independiente de decisiones sensibles. |
| N21 | Preparar, evaluar y activar el modelo operativo cuando haya suficientes eventos reales y representativos. |
| N22–N23 | Reportes operativos completos y cierre/continuidad anual ensayados y aprobados. |
| N24–N25 | Cola durable de OCR, diagnóstico de servicios y mediciones de calidad/tiempo. |
| N26–N28 | Configuración y seguridad de producción, respaldo completo, recuperación y versión reproducible con pruebas de despliegue/carga/concurrencia. |
| N29–N30 | Piloto con personal, mediciones del proyecto y expediente académico/institucional. La documentación técnica resumida ya está consolidada. |
| N31–N32 | Evaluar separación física de libros y transferencias con envío/recepción en dos pasos, si el alcance lo exige. |
| N33–N34 | Stock mínimo/reposición e importación de movimientos nativos CSV/Excel, sujetos a necesidad confirmada. |
| N35–N36 | Notificaciones y tratamiento de desconexiones/operación sin conexión, sujetos a necesidad confirmada. |

No es necesario convertir todas las mejoras condicionales en requisito de la siguiente entrega. La prioridad inmediata es dataset/modelo histórico, seguido de áreas y puesta en operación real, manteniendo las validaciones académicas e institucionales necesarias.

## Comprobaciones y límites

En el avance HIL del 18/10 se registraron **32 pruebas backend y 13 frontend aprobadas**, compilación correcta, ensayo restaurado, aplicación secuencial y verificación de consultas. Los datos, fotos y filas ajenas a los objetivos quedaron protegidos. Estas pruebas no se presentan como una nueva auditoría integral de todos los módulos.

Hay antecedentes de piloto PostgreSQL aislado y herramientas de reproducción del cálculo. Un piloto técnico con datos ficticios no mide adopción institucional ni la precisión del detector con casos humanos. Continúan pendientes el piloto con el personal y las mediciones contra evidencia independiente.

El sistema aún necesita decisiones institucionales sobre unidades, participantes, cierres, conteos y umbrales. Una cifra digitalizada no acredita ubicación física, y una puntuación de rareza no identifica fraude ni autoría.

## Evidencia y mantenimiento

El [perfil de datos y sus huellas](../backend/backups/documentacion_consolidada_20261018/archivos_tecnicos/evidencias/corte-datos-entrenamiento-2026-10-18.json) conserva la consulta utilizada. El [archivo histórico de documentación](../backend/backups/documentacion_consolidada_20261018/documentacion_anterior.zip) contiene los detalles de tareas, casos, informes y pruebas anteriores.

Los planes aplicados y resultados de HIL permanecen en `backend/backups/aplicacion_hil_20261014/`; la cola y verificaciones del 18/10, en `backend/backups/revision_avisos_hil_20261018/`. No reejecutar planes aplicados para regenerar documentación. Nuevos resultados detallados deben guardarse como evidencia técnica; los avances narrativos se actualizan aquí y en los otros dos documentos vigentes.
