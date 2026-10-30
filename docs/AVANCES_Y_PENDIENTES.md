# Avances y pendientes del proyecto

**Corte documental: 29/10/2026, Bolivia.** [Funcionamiento y datos actuales](../README.md) · [Resumen del HIL](RESUMEN_HIL.md).

Este resumen sustituye los informes narrativos de avance anteriores. Conserva lo vigente y las limitaciones conocidas; una propuesta no se considera implementada por aparecer en este documento.

## Diagnóstico de cierre del 29/10/2026

La comprobación actual consultó PostgreSQL en solo lectura: cero huérfanos, cero posiciones históricas duplicadas, dos aperturas consistentes y 693 imágenes históricas referenciadas presentes. Se mantienen 11.918 movimientos, 117 tratamientos con marca y 8.367 elegibles. Pasaron 302 pruebas backend, con una prueba de concurrencia omitida; 85 casos frontend pasaron en dos ejecuciones, tras repetir los 20 del módulo de inventario por un timeout al iniciar su worker. TypeScript/Vite compila y once consultas GET con PostgreSQL devolvieron HTTP 200. Esto no equivale a una prueba de carga ni a un piloto con personal.

Orden propuesto para el cierre, conservando las referencias N01–N36:

1. **C01 completada el 29/10:** corregido el tipo de catálogo en coincidencias exactas, alias y sugerencias; siete nodos «Área: Ventas» reparados con siete auditorías. Cero operaciones clasificadas como áreas.
2. **C02 implementada; validación documental pendiente:** selección explícita de fila/foto, evidencia con huella, revisión de cambios y misma fuente para inventario/reportes/apertura. Permanecen 397 propuestas y cero confirmaciones documentales; 359 bases pasan controles y 38 están bloqueadas. N03, cobertura del archivo, requiere evidencia institucional.
3. **C03 implementada; validación institucional pendiente:** administración de áreas, catálogo documental, alias y adscripción con auditoría; falta confirmar áreas/personas/ámbito de permisos y resolver documentalmente las 32 inferencias y otros 28 avisos.
4. **C04 implementada; aceptación en piloto pendiente:** rectificaciones de transferencias, entregas y ventas/retornos mediante compensaciones vinculadas, disponibles para Administrador; libro, grafo, CSV, informe y balances anuales reconciliados.
5. **C05 preparada y circuito técnico verificado:** nueva consulta de prioridades y ficha imprimible, sin aprobar ni registrar conteos. Las 26 unidades sin ubicación incluyen 20 del registro «PRUEBA E91159» y 6 de «Testimonios», pendientes de cotejo. Se ensayaron en PostgreSQL aislado 14 etapas conectadas y cierre/reapertura/versionado. Siguen pendientes conteo, ubicación, documentos y aceptación con personal; no se crearon operaciones ficticias en la base institucional. El cierre real 2026 está bloqueado porque la gestión no terminó.
6. **C06 implementada; etiquetado y aprobación pendientes:** nuevo flujo de estudios documentales y del detector, selección reproducible sin puntuaciones, referencia humana separada de HIL, revisión por otra cuenta, fotos con huella y exportación verificable. Las métricas permanecen pendientes hasta completar la muestra. Hay cero estudios/etiquetas independientes reales y cero revisiones analíticas previas; el diseño temporal 2025 sigue con 3/3 filas. No se declara oficial el dataset por este avance.
7. N24–N30: versión reproducible, instalación de producción, respaldo final y restauración, permisos, carga/concurrencia y aceptación. C01 generó un nuevo respaldo completo restaurado del estado previo a sus siete correcciones; el respaldo de la entrega final sigue siendo una etapa posterior.

N21 depende del alcance operativo de IA: hay un evento elegible, frente al mínimo de 125 y 14 días. No es apropiado suplirlos con OCR o registros ficticios. Las mejoras condicionales N18/N31–N36 no pasan a ser automáticamente bloqueadores. [Diagnóstico detallado y criterios de cierre](../outputs/diagnostico-cierre-20261029/Diagnostico_para_terminar_el_sistema.md), [plan estructurado](../outputs/diagnostico-cierre-20261029/Plan_de_cierre.json) y [evidencia técnica](../backend/backups/diagnostico_cierre_20261029/estado_cierre.json). No se cambiaron datos de negocio ni se aplicaron correcciones en esta revisión.

### Cierre de C01, 29/10/2026

Se reparó la causa del prefijo incorrecto: el resolver ahora utiliza el tipo de departamento/operación en las tres vías del catálogo. Las sugerencias conservan HIL y las unidades históricas inactivas siguen disponibles para interpretar el papel. Se ensayó en la restauración del respaldo `respaldo_20261029T143219017715Z` y después se aplicó el plan congelado a siete filas: 432, 4272, 4398, 4721, 5050, 5540 y 7313. El nodo quedó «Salida: Ventas», con `area_estado=NO_APLICA`; el texto AREA y la primera lectura se conservaron.

La reconciliación comprobó las demás filas/tablas, fechas, cantidades, saldos, tratamientos y archivos privados sin cambios. Se añadieron siete auditorías. Pasaron 73 pruebas del clasificador/Kárdex/trazabilidad/HIL y diez consultas GET con PostgreSQL, incluido el historial de revisión. Se mantienen 117 tratamientos con marca, 8.367 elegibles y los dos modelos consistentes con sus cortes. Cuatro filas elegibles incorporarán su nodo corregido al construir un corte posterior; no se alteraron los datasets congelados ni el cuaderno experimental. [Resultado](../backend/backups/c01_operaciones_catalogo_20261029/resultado.json) y [verificación](../backend/backups/c01_operaciones_catalogo_20261029/verificacion.json). C02 se implementó posteriormente; sus confirmaciones documentales y la cobertura siguen pendientes.

### Implementación de C02, 29/10/2026

Se añadió la fuente explícita por artículo: fila, documento/foto, orden, gestión, referencia, motivo, responsable y huella de evidencia. Se rechazan decisiones desactualizadas y se conserva el cierre elegido si se incorpora una hoja antigua posteriormente. Una selección retirada/desactualizada bloquea nuevas aperturas históricas; una apertura ya utilizada permanece fija. Inventario, libro, dashboard e informe consumen la misma selección.

La migración s94e53afb168 se ensayó con upgrade/downgrade/upgrade en respaldo restaurado y se aplicó sin alterar datos, secuencias, evidencias ni modelos. Pasaron 331 pruebas backend (una omitida), 86 frontend, TypeScript/Vite y nueve GET de solo lectura. Los escenarios de aprobación se revirtieron en QA: permanecen 397 propuestas, cero confirmaciones, 38 bases bloqueadas y 8.367 elegibles. C02 queda **implementada y pendiente de validación documental**; N03 no se considera certificada. [Uso y evidencia](../outputs/cierre-documental-20261029/Cierre_documental_C02.md).

### Implementación de C03, 29/10/2026

Inicio → Áreas y catálogos permite altas, edición, bajas/reactivación e historial; separa ubicaciones de stock del catálogo documental. Las bajas protegen stock, custodias y usuarios activos, con bloqueo compartido durante el uso del área. La adscripción de cuentas conserva motivo y autoría y no sustituye la matriz institucional de permisos.

Migración t05f64b0c279 ensayada y aplicada sin cambios en datos previos: dos áreas registradas (solo Galería activa, Cedoal de baja), C+C histórica, 64 alias sin nuevas confirmaciones, 32 inferencias, 117 marcas HIL y 8.367 elegibles. Pasaron 347 pruebas de la suite backend (una omitida), 28 focalizadas posteriores, 92 frontend, compilación y diez GET PostgreSQL. Se ensayó concurrencia en QA y se revisó la interfaz en escritorio/móvil con datos simulados. [Detalle y pendientes institucionales](../outputs/areas-catalogos-20261029/Administracion_areas_C03.md).

### Implementación de C04, 29/10/2026

Se añadieron rectificaciones logísticas de cantidad, áreas y contexto de transferencias/custodias/eventos. Los originales se conservan y cada compensación registra valores previos/nuevos, documento, motivo y autor. Se protegen saldos, ventas/retornos posteriores, versión, idempotencia, concurrencia y periodo abierto.

La migración u16a75c1d380 se ensayó y aplicó con reconciliación de datos. Se verificaron correcciones sucesivas, anulaciones, contexto, saldo externo/institucional, libro/CSV/grafo y conservación del balance/huella anterior a una rectificación de venta. Las pruebas de PostgreSQL se revirtieron en QA. C04 queda implementada con aceptación de uso real pendiente en C05; N14 (adjuntos) y N20 (aprobación independiente) conservan sus pendientes. [Guía y evidencia](../outputs/rectificaciones-logisticas-20261029/Rectificaciones_logisticas_C04.md).

### Preparación y piloto técnico de C05, 29/10/2026

Se implementó Inicio → Preparación del inventario, disponible para los tres roles: prioridades por artículo, saldo operativo/documental, búsqueda, filtros, enlace al detalle y ficha imprimible. Los campos de conteo, fecha, participantes, acta y firmas quedan vacíos; imprimir no modifica stock. La marca de posible prueba por nombre no excluye automáticamente el registro ni confunde «Testimonios» con «test».

El circuito conectado en PostgreSQL aislado confirma fuente y conciliación QA, entradas, venta, devolución, transferencia, entrega, ventas y retornos externos, cuatro rectificaciones con reintentos y coherencia de libro/grafo/CSV/informe. Termina con 20 unidades: 10 en Galería QA, 7 en Depósito QA y 3 en custodia. Se verifican cierre, bloqueo del periodo, reapertura, balance conservado y cierre versión 2. Se añadió el bloqueo de conciliación inicial tras transferencias/rectificaciones y de apertura física durante una gestión cerrada.

La revisión de solo lectura confirma dos aperturas, cero conciliaciones reales, 397 fuentes sin confirmar y 38 bases bloqueadas. Las 20 unidades del artículo «PRUEBA E91159» requieren aclarar su condición; las 6 de «Testimonios», conteo físico actual y ubicación. El saldo documental 8 no sustituye el saldo operativo 6 ni acredita una diferencia física. C05 no se declara institucionalmente terminado. Continúan C02/C03 y N14; el siguiente bloque técnico es C06, validación documental y del detector con evidencia independiente. [Guía, protocolo, resultados y evidencias](../outputs/preparacion-inventario-20261029/Preparacion_y_piloto_C05.md).

Comprobación final de C05: 367 pruebas backend aprobadas y una omitida por requerir PostgreSQL; 155 aprobadas en PostgreSQL aislado sin omisiones, incluida la concurrencia del cierre; 105 frontend y compilación correctas. Se comprobaron siete consultas GET sobre el estado real y la pantalla en computadora, móvil e impresión para los tres roles, con API simulada. Todas las tablas, secuencias y 927 archivos privados institucionales se conservaron. El respaldo previo del estado actual fue restaurado y verificado; el esquema permanece en u16a75c1d380.

### Implementación de C06, 29/10/2026

Inicio → Validación del proyecto permite preparar estudios de concordancia documental vigente y de utilidad del detector, con un máximo de 100 filas por estudio. Se congelan población, selección por semilla/ID, datos y fotos. El detector utiliza únicamente evaluación reservada de una versión consistente; el sorteo no selecciona por puntuación. No se muestran predicción, puntuación ni decisiones analíticas/HIL anteriores. Las etiquetas nuevas no cambian HIL, libro ni modelo.

El revisor debe usar otra cuenta autorizada, distinta del preparador y del entrenador de esa versión, y declarar independencia con motivo y respaldo. La identidad distinta no garantiza por sí sola independencia fuera del flujo. Las revisiones conservan historial y rechazan versiones desactualizadas. Una fotografía ausente o modificada mantiene pendientes las métricas; las dudas y errores documentales no se retiran del denominador. La concordancia por fila no mide exactitud de la primera extracción OCR. Precisión, recall y F1 se refieren a la muestra completada, con inusual relevante como positivo; no se extrapolan al archivo ni miden fraude.

La exportación incluye población de identificadores, filas y decisiones con procedencia, permitiendo reproducir la selección y verificar su huella. Se preservó el estado real: cero estudios/etiquetas nuevos, cero revisiones analíticas previas, modelo consistente, 8.367 elegibles y 927 archivos privados iguales. Pasaron 372 pruebas backend, una omitida en SQLite; 160 PostgreSQL sin omisiones; 110 frontend, compilación y cinco GET reales. La comprobación focalizada final del informe y su selección aprobó cinco casos. No hubo migración nueva ni cambios de datos institucionales.

Siguen pendientes el protocolo aprobado, cotejos y etiquetas reales, las mediciones específicas del OCR original y del grafo si se requieren, el diseño temporal suficiente, la interpretación y la aprobación/publicación del dataset. C06 no se declara evaluado institucionalmente; el siguiente bloque técnico es C07, una entrega instalable y comprobada. [Guía completa y protocolo](../outputs/validacion-proyecto-20261029/Validacion_independiente_C06.md).

### Evaluación integral para defensa, 29/10/2026

Se volvieron a ejecutar 372 pruebas backend aprobadas (una omitida por requerir PostgreSQL), 110 frontend, compilación y análisis estático sin errores bloqueantes. Se conserva el piloto C06 de 160 pruebas PostgreSQL sin omisiones; no se repitió ese piloto en esta evaluación. Diecinueve GET actuales respondieron correctamente y la foto sin sesión fue rechazada. Se comprobaron las 693 rutas de fotos históricas activas, tablas, secuencias y 927 archivos contra el respaldo restaurado, sin cambiar datos ni modelos.

La auditoría actual del entorno Python reporta 19 avisos en cinco paquetes, con 18 identificadores distintos; certifi aparece duplicado. Npm no reportó vulnerabilidades conocidas. Los avisos corresponden a certifi, dnspython, filelock, pypdf y setuptools; no todas son importaciones directas de la aplicación. Hay que determinar su alcance y actualizar o retirar las dependencias necesarias con verificación de compatibilidad. El cero de la auditoría del 18/10 es un antecedente de aquella fecha, no un resultado vigente. Esta revisión no verificó la explotabilidad de cada aviso ni cambió las bibliotecas.

Tres lecturas sucesivas, sin concurrencia de las suites generales, dieron medianas de 2,769 s para catálogo, 4,255 s para perfil analítico y 5,737 s para informe institucional. Son mediciones locales ASGI/PostgreSQL, sin red ni navegador; no se presentan como prueba de carga. El sistema tiene funciones suficientes y evidencia técnica, pero todavía no hay aceptación con usuarios, etiquetas independientes o dataset aprobado. La valoración propia de preparación para defensa es 7,4/10, con pesos publicados; no es una nota oficial ni un porcentaje de avance. [Evaluación completa y prioridades](../outputs/evaluacion-integral-20261029/Evaluacion_del_sistema_para_grado.md). C07 sigue pendiente y prioriza una entrega reproducible con dependencias revisadas; el respaldo actual ya está restaurado y verificado.

### Revisión de organización visual y propuestas, 29/10/2026

Por petición del titular se revisaron 16 pantallas en escritorio y móvil, más historial e HIL de artículos: 36 capturas con datos reales mediante acceso local exclusivamente de lectura. No aparecieron errores JavaScript ni fallos API. Los catálogos renderizan 398 tarjetas sin paginación; Analítica histórica alcanza 8.461 px y 89 controles desplegados en escritorio. Accesos desborda en móvil (450 px frente a 390 px). También se identificaron tarjetas sin semántica nativa de teclado y 116 apariciones de !important en la hoja global, con estilos particulares en cada vista.

Se prepararon tres propuestas interactivas: Continuidad ordenada, Archivo editorial y Mesa de trabajo. Se recomienda la primera para conservar cabecera, marca, azul y distribución central con tres accesos principales, agrupando herramientas y separando tareas. Las tres se comprobaron en escritorio/móvil, con búsqueda, selección, pestañas y foto real; no llaman a las API del sistema ni guardan operaciones. Se conservaron tablas, secuencias y 927 archivos. No se aplicó un rediseño al frontend en uso. [Revisión detallada y orden de implementación](../outputs/revision-diseno-20261029/Revision_visual_y_opciones.md). Los pendientes institucionales y de C07 mantienen sus condiciones.

## Avance conseguido

| Bloque | Resultado |
|---|---|
| Digitalización | Tres tandas incorporadas, fotos y procedencia conservadas, controles de páginas/títulos y reintentos idempotentes. |
| Calidad documental | Cola inicial de 399 tratada: 283 sin avisos y 116 con marca. N01 añade una ausencia documental cotejada: 117 marcas vigentes y cero avisos sin categorizar. |
| Inventario y operación | Base histórica separada del stock operativo, entradas/salidas con participantes, áreas, transferencias, devoluciones, custodia y ajustes documentados. |
| Auditoría y reportes | Reglas para histórico y operación digital, casos de seguimiento, libro por artículo, CSV, filtros por gestión, grafo, informe y cierres. |
| Analítica | Nueva versión histórica retrospectiva entrenada y verificada el 20/10 con el corte HIL actual. Evaluación humana pendiente; modelo operativo sin entrenamiento ni activación. |
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

## Entrenamiento de Isolation Forest y evaluación pendiente

El 20/10 se confirmó en modo de solo lectura el corte de **8.367 movimientos de 356 artículos entre 2005 y 2025**, sin avisos HIL entre los elegibles. Por instrucción del titular se entrenó la versión retrospectiva **`46e3683e-0210-4917-aadf-656af9dd2e2c`**: 5.030 filas de entrenamiento, 1.722 de calibración y 1.615 de evaluación reservada. Se conservaron 200 árboles, semilla 42 y revisión provisional del 5 %.

El módulo histórico ya utiliza cantidad, comparación con referencias, desviación robusta, rareza de nodo y artículo/nodo, ausencia documental de nodo y dirección del movimiento. Las referencias estadísticas se calculan con entrenamiento. Existen modalidades retrospectiva y temporal, con separación y controles de lotes.

Se generaron dataset candidato, particiones, diccionario, configuración, huellas y nueva versión con artefacto reproducible. La integridad y reproducción fueron **CONSISTENTES**. Hay 359 alertas puntuadas: 165 de entrenamiento, 83 de calibración y **111 de evaluación reservada**. En esta última partición, 1.376/1.615 movimientos utilizan respaldo global por carecer de referencia propia de artículo/dirección en entrenamiento. Esa limitación debe incluirse al interpretar los resultados; estabilidad y cantidad de alertas no miden precisión.

Se conserva un respaldo coherente previo y se comprobó que solo cambiaron las tablas analíticas y auditoría; los datos documentales y los 926 archivos privados anteriores permanecieron intactos. Las evidencias están en [el expediente técnico del entrenamiento](../backend/backups/entrenamiento_historico_20261020/resultado.json). No se registraron etiquetas ni conclusiones humanas.

Para presentar la calibración experimental se ejecutó el 28/10 un cuaderno reproducible con las siete variables del corte congelado: 8.367 filas y particiones originales. Reproduce puntuaciones con error máximo de orden 10⁻¹⁷ y el umbral 0,6115351601984308. Compara siete objetivos de revisión (1–15 %) y doce ajustes (50/100/200/400 árboles × semillas 42/43/44) utilizando entrenamiento/calibración para el diagnóstico. No elige parámetros usando evaluación reservada ni cambia la configuración activa. Seis figuras muestran particiones, distribuciones, cuantil, sensibilidad, estabilidad/costo y cobertura de evaluación. El cuaderno conserva 111 alertas de evaluación y 1.376 movimientos con respaldo global, sin inventar Ground Truth o métricas supervisadas. [Informe HTML](../outputs/calibracion-isolation-forest-20261028/Calibracion_Isolation_Forest.html), [notebook ejecutado](../outputs/calibracion-isolation-forest-20261028/Calibracion_Isolation_Forest.ipynb) y [evidencia de ejecución](../backend/backups/calibracion_notebook_20261028/verificacion.json). Este avance técnico no cierra los pendientes institucionales y humanos enumerados a continuación.

El siguiente ciclo debe completar:

1. Aprobación del marco y dataset institucional; el corte técnico ya está congelado y documentado.
2. Evaluación humana de alertas y muestra de control; medir utilidad y ajustar el umbral con evidencia.
3. Etiquetado independiente y representativo para las métricas académicas que requieran positivos y negativos conocidos.
4. Diseño temporal viable: reservar 2025 deja solo 3 filas de calibración y 3 de evaluación tras la purga documental, por debajo de los mínimos.
5. Informe de resultados y decisión sobre uso. El modelo histórico no pasa automáticamente a ser el modelo de operaciones digitales de 2026.

La categorización HIL no habilita los 116 casos marcados ni los 40 artículos excluidos. La versión anterior conserva su corte original. El entrenamiento del 20/10 no modificó movimientos ni levantó exclusiones; el modelo operativo continúa pendiente de datos suficientes.

## Plan de continuidad resumido

Se conservan los identificadores N01–N36 del plan anterior para no perder referencias. Los trabajos no revalidados en este corte mantienen su condición pendiente o de comprobación; no se presume que sigan idénticos todos los hallazgos del 13/10.

| IDs | Trabajo pendiente o condición de cierre |
|---|---|
| N01 | Completada el 28/10: fechas ausentes/parciales/ilegibles, texto y precisión, HIL, filtros, reportes, grafo y selección analítica. Migración ensayada y aplicada; movimiento 12272 normalizado con primera lectura y auditoría conservadas. No equivale a cotejar todas las fechas del archivo. |
| N02–N03 | Flujo de selección/revisión de fuente implementado el 29/10 (C02). Faltan las confirmaciones documentales por artículo y la certificación de cobertura del archivo/catálogo. |
| N04 | Revisión asistida de la cola HIL acordada completada; conservar marcas y resolver nuevas evidencias sin repetir cotejos masivos. |
| N05–N06 | Muestra documental de investigación y aprobación/publicación institucional del dataset oficial. Corte técnico, particiones y diccionario del 20/10 disponibles. |
| N07–N08 | Formalizar/evaluar el grafo y preparar etiquetado independiente para medir resultados de Isolation Forest. |
| N09–N10 | Nueva versión retrospectiva entrenada y verificada el 20/10. Pendientes evaluación humana y diseño temporal con particiones suficientes e independientes. |
| N11–N12 | Administración de áreas/catálogo/alias y adscripción implementada en C03. Pendientes validación de unidades/personas, matriz de permisos/ámbito y cotejo de inferencias/excepciones. |
| N13–N14 | Conteo y conciliación reales de 2026; adjuntar actas y documentos de negocio. |
| N15 | Simplificar flujos y estados para el personal; el HIL ya distingue categorías y vigencia. |
| N16–N17 | Rectificaciones de transferencias, entregas y ventas/retornos implementadas en C04; pendientes aceptación y validación con documentos reales dentro de C05. |
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

No es necesario convertir todas las mejoras condicionales en requisito de la siguiente entrega. Se avanza una tarea por vez. Tras N01, el titular priorizó revisar las áreas y siglas de los Kárdex históricos; N02, la fuente de cierre documental confirmada, sigue pendiente. Continúan N03/N05 y la evaluación humana y temporal, además de áreas y puesta en operación real.

### Revisión de áreas y siglas históricas, 28/10/2026

Consulta de solo lectura de los 11.859 movimientos históricos activos: 60 avisos de área en 40 artículos, con 36 equivalencias sin confirmar, 17 lecturas inciertas, 6 marcas no interpretadas y 1 efecto indeterminado. Todos conservan tratamiento HIL; no se declaró resuelta su identidad institucional. Hay 11 departamentos y 7 operaciones en el catálogo, con 23 alias marcados como confirmados y 41 sugeridos. Una bandera de la base no acredita por sí sola aprobación institucional.

Se cotejaron siete fotos representativas. En una fila, «Archivo Fonográfico» respalda la abreviación «Arch. Fon.», pero no define su dependencia institucional. Hay grafías compatibles con C+C transcritas CTC/CtC, candidatas a corrección puntual. CDP/COP y DIF. siguen necesitando aclaración. Se detectaron además siete nodos «Área: Ventas»: el resolver no distingue departamentos de operaciones del catálogo. Quedan pendientes su corrección técnica y revisión auditada; también debe conservarse como no confirmada la sugerencia SALIDA→Sala.

No se modificaron movimientos, equivalencias, tratamientos, exclusiones ni modelos. La revisión documental de áreas no cierra la administración operativa, participantes y permisos de N11–N12. [Informe con casos y fotos](../outputs/revision-areas-historicas-20261028/Revision_areas_historicas.md) y [extracción verificable](../backend/backups/revision_areas_historicas_20261028/revision.json). El cotejo fue de siete fotos, no una nueva revisión visual de todas las hojas afectadas.

### Aplicación posterior de asignaciones inferidas, 28/10/2026

El titular autorizó después asignar por parecido, frecuencia y correlaciones, y confirmó C+C como área antigua que ya no existe. Se aplicó un plan congelado de **32 asignaciones inferidas**: Capacitación 19, C+C 4, Galería 3, CEDOAL 3, CID 2 y Sala 1. Se ponderan afinidad de texto/regla (70 %), frecuencia relativa del artículo (16 %), hoja (10 %) y archivo (4 %), con mínimos de afinidad/margen. Son reglas heurísticas documentadas, sin exactitud validada contra Ground Truth. Las inferencias no votan como referencias ni se convierten en alias globales.

Quedan 28 casos sin asignación suficiente: 13 equivalencias, 8 lecturas inciertas, 6 marcas y 1 efecto indeterminado. Los otros 32 mantienen el aviso bajo la categoría **Área asignada por correlación**, con literal, candidatos, soporte, autor y huella del plan. El HIL y el grafo muestran su condición inferida; cambiar otro campo en el formulario ya no envía el nodo sin cambios como confirmación manual. Se conserva el tratamiento anterior en la auditoría.

Se verificó un respaldo completo con restauración, se ensayó el plan en esa copia y luego se aplicaron 32 revisiones y auditorías en una transacción. Permanecen las demás filas, catálogos, alias, lecturas, fechas, cantidades, saldos, exclusiones y 927 archivos privados. La cola mantiene 117 filas con marca, cero sin categorizar/recategorizar y los mismos 8.367 elegibles. El modelo congelado sigue consistente. Suite general: 301 pruebas backend aprobadas/una omitida y 84 frontend; tras añadir la visualización explícita en trazabilidad, sus 6 pruebas backend y 5 frontend pasan. Compilación correcta, cinco consultas GET sobre PostgreSQL y comprobación visual de HIL, grafo y foto sin escrituras.

Los siete nodos «Área: Ventas» se corrigieron posteriormente en C01; este plan de inferencias no completa N11–N12 ni confirma cierres documentales. [Detalle de asignaciones y casos restantes](../outputs/revision-areas-historicas-20261028/Asignacion_areas_historicas.md), [aplicación](../backend/backups/revision_areas_historicas_20261028/resultado_asignacion.json) y [verificación](../backend/backups/revision_areas_historicas_20261028/verificacion_asignacion.json).

### Cierre técnico de N01, 28/10/2026

Se admiten fechas históricas `null` y texto parcial/ilegible sin completarlo por secuencia. La API y la base mantienen obligatoria la fecha digital. La revisión HIL registra ausencia, lectura parcial o ilegible, impide confirmar una fecha hipotética sin lectura completa y conserva la primera extracción. Reportes y CSV separan **Sin gestión confirmada**; el grafo permite **Sin fecha confirmada** y conserva las fechas técnicas como antecedentes. La cobertura y el perfil del dataset no asignan esas filas a un año acreditado.

Se revisó la foto del caso 12272, ya identificado en N01. Se retiró la fecha técnica vigente, conservando `2023-01-01` en originales y antecedentes. Tiene la nueva categoría **Dato ausente en el documento**. Se modificó una fila y se añadió una auditoría; permanecen las demás filas, cantidades, saldos, aperturas, 116 tratamientos anteriores y modelos. Siguen 8.367 elegibles; el modelo congelado conserva sus resultados y diagnóstico consistente.

La migración `r83d42fea057` se ensayó en la restauración del respaldo del 28/10 mediante upgrade/downgrade/upgrade y normalización revertida. Se verificó que una reversión con nuevos datos documentales se bloquea. Se ejecutaron 283 pruebas backend y 81 frontend aprobadas, compilación correcta y consultas PostgreSQL de los consumidores afectados. Una prueba general de concurrencia sigue omitida en SQLite; no se presenta como ejecutada en esta entrega. [Reconciliación de aplicación](../backend/backups/n01_fechas_20261028/resultado_aplicacion.json) y [verificación de la instalación](../backend/backups/n01_fechas_20261028/verificacion_instalacion.json).

## Comprobaciones y límites

La auditoría integral posterior del 18/10 corrigió altas no atómicas y códigos repetibles, existencias resumidas, avisos que contaban notas/anulaciones, y consultas de evidencia que evaluaban artículos ajenos. Retiró 30 archivos sin uso y dependencias innecesarias, actualizó paquetes con avisos de seguridad y añadió dos índices, diagnóstico de conexión y comprobaciones automáticas. El detalle técnico vigente está en [el README](../README.md#auditoría-integral-del-18102026).

La auditoría del 18/10 dejó el esquema en `q72c31ed9f46`; N01 lo actualizó a `r83d42fea057` el 28/10. La auditoría anterior comparó 44 tablas y secuencias, con cambios solo en `alembic_version`, y conservó 926 archivos privados, los 116 tratamientos HIL y los 8.367 elegibles. La aplicación focalizada de N01 se documenta por separado arriba.

Comprobación final: 274 pruebas backend aprobadas y una omitida, 79 frontend, 101 pruebas PostgreSQL aisladas y 66 consultas de lectura sobre datos reales con resultado esperado. Compilación y análisis estático sin errores; cero vulnerabilidades conocidas reportadas por las auditorías Python/npm al cierre. La retirada de cuatro pruebas frontend corresponde al único componente huérfano eliminado, sin reducir la cobertura de los componentes utilizados.

Esto atiende parte de N24 y N26–N28, pero no certifica producción ni reemplaza N29–N30. Siguen pendientes un despliegue ensayado completo, carga/concurrencia representativa, piloto con personal, calibración y mediciones del detector. Algunas consultas analíticas completas tardaron alrededor de 1,7–2,3 segundos en el equipo local; deben medirse con usuarios simultáneos antes de decidir caché o procesamiento adicional. No se implementó caché que pueda devolver una revisión HIL desactualizada.

En el avance HIL del 18/10 se registraron **32 pruebas backend y 13 frontend aprobadas**, compilación correcta, ensayo restaurado, aplicación secuencial y verificación de consultas. Los datos, fotos y filas ajenas a los objetivos quedaron protegidos. Estas pruebas no se presentan como una nueva auditoría integral de todos los módulos.

Hay antecedentes de piloto PostgreSQL aislado y herramientas de reproducción del cálculo. Un piloto técnico con datos ficticios no mide adopción institucional ni la precisión del detector con casos humanos. Continúan pendientes el piloto con el personal y las mediciones contra evidencia independiente.

El sistema aún necesita decisiones institucionales sobre unidades, participantes, cierres, conteos y umbrales. Una cifra digitalizada no acredita ubicación física, y una puntuación de rareza no identifica fraude ni autoría.

## Evidencia y mantenimiento

El [perfil de datos y sus huellas](../backend/backups/documentacion_consolidada_20261018/archivos_tecnicos/evidencias/corte-datos-entrenamiento-2026-10-18.json) conserva la consulta utilizada. El [archivo histórico de documentación](../backend/backups/documentacion_consolidada_20261018/documentacion_anterior.zip) contiene los detalles de tareas, casos, informes y pruebas anteriores.

Los planes aplicados y resultados de HIL permanecen en `backend/backups/aplicacion_hil_20261014/`; la cola y verificaciones del 18/10, en `backend/backups/revision_avisos_hil_20261018/`. No reejecutar planes aplicados para regenerar documentación. Nuevos resultados detallados deben guardarse como evidencia técnica; los avances narrativos se actualizan aquí y en los otros dos documentos vigentes.
