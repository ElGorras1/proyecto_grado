# Protocolo de evaluación del proyecto

Preparación del 31/10/2026, conforme al capítulo I aprobado, secciones 1.8.5–1.8.7.
Este documento organiza la ejecución. No contiene etiquetas, mediciones de personas
ni aprobaciones institucionales realizadas. El desarrollo del sistema es individual;
el personal que coteje documentos participa en la evaluación, no como un equipo de desarrollo.

## Marco y selección

1. Identificar la población autorizada, periodo, unidad, legibilidad y exclusiones.
   Separar movimientos documentales, artículos con historial completo y evaluación del detector.
2. Congelar identificadores, procedencia, versión del código, fotografías y huellas.
3. Para indicadores documentales por movimiento, recalcular la muestra para población
   finita con Z=1,96, p=q=0,50 y error=0,05. El valor preliminar 379 suponía N=25.000.
   La consulta técnica del 31/10 cuenta 11.859 históricos activos con ruta de foto y
   recomienda 373; la institución debe confirmar que ese marco es el autorizado y elegible.
4. Usar selección aleatoria simple sin reemplazo, conservar semilla, población y muestra.
   El límite técnico es 5.000 filas por estudio; se rechaza pedir más que la población.
   Este límite no fija el tamaño estadístico ni el número de casos del detector.
5. Para historiales, seleccionar artículos del marco aprobado e incluir todos sus
   movimientos disponibles. El tamaño documental por movimiento no se traslada a artículos.

## Cotejo documental y extracción

La herramienta DOCUMENTAL compara la transcripción vigente. Si se informa exactitud
de extracción original, conservar por separado primera lectura, fotografía y referencia
humana; medir los mismos campos legibles antes y después de las correcciones.
Definir con la institución los campos obligatorios y las relaciones esperadas. Registrar
correcto, incorrecto, ausente y no evaluable, con razón y denominador para cada indicador.
No utilizar concordancia vigente como si fuera exactitud original, CER o WER.

El tiempo de extracción separa carga, espera del proveedor, extracción, validación y
revisión humana; registrar fallos y reintentos, tamaño y número de páginas. Las medianas
locales de consultas del servidor no sustituyen tiempos de tareas con usuarios.

## Relaciones del grafo e historiales

Preparar las relaciones esperadas desde documentos antes de contrastar el grafo.
Registrar artículo, evento, origen, destino, tipo de vínculo y evidencia; distinguir
evento documental, operación digital, agregación visual y ubicación confirmada.
Anotar relaciones correctas, ausentes, adicionales y no verificables. Los movimientos
no equivalen automáticamente al número de aristas. Para continuidad, registrar todos
los eventos del artículo y el periodo cuya cobertura se pudo verificar; no declarar
completo un archivo físico cuya cobertura todavía se desconoce.

## Referencia independiente del detector

Los estudios nuevos, versión 2, usan las definiciones aprobadas:

| Clase | Criterio |
|---|---|
| NORMAL | Respaldo suficiente y ninguna desviación verificada respecto de criterios institucionales definidos. |
| ANOMALO | Inconsistencia verificada de cantidad, fecha, tipo de operación o área respecto de documentos. Registrar criterio, motivo y referencia. |
| INDETERMINADO | Respaldo insuficiente. Someter a segunda revisión; si persiste, informarlo fuera del denominador principal. |

Fijar modelo, población y umbral antes de mostrar etiquetas. La muestra principal no
sobremuestrea alertas; los casos priorizados por riesgo se analizan por separado.
El preparador y el entrenador no pueden etiquetar desde sus cuentas. La persona que
revise debe ser independiente y no haber visto predicciones de esos casos. La vista
omite puntuación y predicción; el protocolo debe controlar también otros accesos y
exportaciones. Una cuenta distinta no demuestra por sí sola independencia personal.

Una etiqueta indeterminada inicial queda pendiente. La segunda revisión exige un
antecedente indeterminado y registrar explícitamente el nuevo cotejo, motivo y respaldo;
no se marca automáticamente. Conservar la cadena de decisiones. Solo al revisar toda
la muestra y comprobar evidencia y modelo, calcular matriz, Precision, Recall y F1
sobre normales y anómalos. Informar seleccionados, evaluables, pendientes e indeterminados
excluidos. Una división indefinida queda sin valor; sin casos evaluables no se inventan ceros.
La afirmación de independencia y el segundo cotejo deben corresponder a acciones reales.

Los estudios versión 1 conservan su sorteo, clases y denominadores. No convertir
LEGITIMO/INUSUAL_RELEVANTE o ERROR_DOCUMENTAL retrospectivamente a las clases del capítulo I.
Las revisiones HIL y las conclusiones analíticas previas no se copian como referencia nueva.

## Particiones y versiones analíticas

La versión histórica del 20/10 se conserva. La auditoría del corte congelado detectó
seis artículos entre conjuntos, sin lotes ni fotografías cruzados. La opción POR_ARTICULO
mantiene en un conjunto cada componente relacionado por artículo, lote o fotografía,
y ajusta estadísticas y bosque solo con entrenamiento. La reconstrucción de asignación
y la comprobación de cruces complementan el control de reproducción.

El experimento local del 31/10, separado del registro operativo, produce 4.689 filas
de entrenamiento, 2.169 de calibración y 1.509 de evaluación, con 214/71/71 artículos
y cero cruces. Todas las filas de evaluación carecen de referencia propia de artículo:
es una prueba de artículos no vistos y utiliza referencias globales. No demuestra
superioridad, precisión ni predicción de eventos futuros. Antes del etiquetado final,
confirmar el propósito de generalización y la versión a evaluar. El diseño temporal
con población insuficiente continúa pendiente; no se rebajan sus controles para entrenar.

## Comparación antes y después

Usar tareas equivalentes de registro, búsqueda y reconstrucción, con participante
identificado por código, caso, instrucciones, fuentes y criterio de éxito. Registrar
tiempo y éxito en ambos procedimientos; conservar tareas incompletas y motivos.
Controlar o declarar orden y familiaridad. Mostrar cambios por pares y número de
pares válidos, sin convertir el diseño cuasiexperimental en una afirmación causal concluyente.

## Evidencia para el capítulo IV

| Instrumento | Registro mínimo |
|---|---|
| F01 Marco y selección | Unidad, periodo, N, criterios, exclusiones, semilla, n y huellas. |
| F02 Cotejo por movimiento | Identificador, campos obligatorios, completitud, relaciones y evidencia. |
| F03 Extracción original y vigente | Campo, primera lectura, lectura vigente, referencia, evaluación y tiempo por fase. |
| F04 Grafo e historial | Artículo, eventos y relaciones esperados/observados, cobertura y resultado. |
| F05 Referencia del detector | Estudio, modelo, etiqueta, criterio, respaldo, autor, independencia y segunda revisión. |
| F06 Comparación de tareas | Participante, caso, orden, tiempos antes/después, éxito y motivos de no finalización. |
| F07 Aceptación | Procedimiento demostrado, observaciones, pendientes, responsables y decisión real. |

El investigador conserva el expediente y prepara el análisis; la institución confirma
fuentes, criterios, participantes y aceptación. Los formularios vacíos y los ensayos QA
son preparación y comprobación técnica, no resultados institucionales.

Referencias técnicas: [separación por grupos](https://scikit-learn.org/1.5/modules/generated/sklearn.model_selection.GroupShuffleSplit.html)
y [métricas de clasificación](https://scikit-learn.org/1.5/modules/generated/sklearn.metrics.precision_recall_fscore_support.html).
El programa usa una implementación propia de componentes; no afirma llamar a GroupShuffleSplit.
