# Sistema de Gestión y Trazabilidad de Activos Operativos

**Fundación Simón I. Patiño · Estado documental: 29/10/2026, Bolivia.**

El sistema digitaliza Kárdex físicos y conserva su evidencia; permite corregir lecturas, consultar movimientos y gestiones, trabajar con inventario actual, transferencias y custodias, generar reportes y apoyar la auditoría mediante reglas e Isolation Forest.

La documentación vigente se reduce a **tres documentos, incluido este README**:

| Documento | Contenido |
|---|---|
| **README — este documento** | Funcionamiento, módulos, datos actuales, roles y operación técnica básica. |
| [Avances y pendientes](docs/AVANCES_Y_PENDIENTES.md) | Qué se completó, qué puede demostrarse y qué falta para terminar y evaluar el proyecto. |
| [Resumen único del HIL](docs/RESUMEN_HIL.md) | Criterios aplicados, correcciones, categorías, evidencia y límites de la revisión. |

## Estado actual de los datos

Última comprobación: 29/10, después de completar N01 y aplicar 32 asignaciones inferidas de áreas históricas el 28/10. Se conservan las cantidades y el modelo histórico del 20/10. La fecha técnica del movimiento 12272 se sustituyó por una ausencia explícita con foto cotejada, primera lectura intacta y auditoría:

| Indicador | Resultado |
|---|---:|
| Movimientos conservados | 11.918 |
| Históricos, incluidos estados no activos | 11.908 |
| Históricos activos | 11.859 |
| Registros digitales sin lote histórico | 10 |
| Movimientos elegibles según los controles analíticos actuales | **8.367** |
| Artículos representados entre los elegibles | **356** |
| Gestiones de los elegibles | **2005–2025** |
| Movimientos HIL tratados, incluida la ausencia documental de N01 | 400 |
| Movimientos de esa cola sin avisos | 283 |
| Movimientos categorizados con marca conservada | 117 |
| Avisos sin categorizar | **0** |

Las tres tandas del escaneo previsto fueron incorporadas. La cobertura total del archivo físico requiere una comprobación institucional; no debe mantenerse como actual la antigua estimación de 30–40 % pendiente. Las cantidades de catálogo, lotes, fotos y movimientos son indicadores diferentes.

La revisión de cierre del 29/10 confirmó 693 rutas de imágenes históricas presentes, cero registros huérfanos, cero posiciones duplicadas y distribución consistente en las dos aperturas. Hay 397 cierres calculados, 359 bases que pasan controles automáticos y 38 bloqueadas; no hay confirmaciones de cobertura registradas. Las dos aperturas suman 26 unidades sin ubicación asignada. El [diagnóstico de cierre](outputs/diagnostico-cierre-20261029/Diagnostico_para_terminar_el_sistema.md) ordena las correcciones y validaciones. Su revisión inicial fue de solo lectura; por instrucción posterior, C01 se completó y se implementó el flujo C02; las confirmaciones documentales y la cobertura física siguen pendientes.

**Categorizar no confirma los datos inciertos.** Los 117 movimientos marcados siguen excluidos de la selección analítica. Los 8.367 elegibles tampoco equivalen a una validación humana exhaustiva de todo el archivo: son el conjunto que supera los controles actuales, antes de separar entrenamiento, calibración y evaluación.

### Fechas documentales: N01 completada el 28/10/2026

El extractor y la base admiten fechas históricas completas, parciales, ausentes e ilegibles. Conservan el texto escrito y la precisión; una fecha incompleta permanece `null`, sin rellenar día, mes o año. Las operaciones digitales siguen exigiendo una fecha. El HIL permite registrar la ausencia o la lectura parcial con motivo y conserva la primera extracción.

Los reportes ofrecen **Sin gestión confirmada** y la trazabilidad **Sin fecha confirmada**. Las fechas técnicas o hipotéticas conservadas no alimentan filtros anuales ni se muestran como fecha del hecho en el grafo. Las filas sin fecha completa quedan fuera del entrenamiento y del cierre documental operable. El dataset de consulta conserva `null`, la procedencia y la precisión; los cortes antiguos del modelo permanecen congelados.

Se cotejó la foto del movimiento 12272, cuya celda FECHA está vacía. Su fecha vigente ahora es ausente; `2023-01-01` permanece en la primera lectura, el antecedente y la auditoría. Solo cambió esa fila y se añadió una auditoría. Se mantienen los 11.918 registros, los 8.367 elegibles, las decisiones anteriores, los saldos y los modelos. El caso agrega una marca **Dato ausente en el documento**, con 117 marcas vigentes y cero avisos sin categorizar.

La migración actual es `r83d42fea057`. Se ensayó con upgrade/downgrade/upgrade en una restauración del respaldo previo, con reconciliación de filas y bloqueo de una reversión que perdería nuevas lecturas. Evidencias en [el expediente de N01](backend/backups/n01_fechas_20261028/resultado_aplicacion.json). Esta tarea no completa N02 ni certifica que todas las fechas del archivo hayan sido cotejadas.

### Áreas históricas: asignación por correlación del 28/10/2026

Por instrucción posterior del titular se asignaron 32 de los 60 movimientos con aviso de área usando parecido, familias de variantes y frecuencias del artículo, la hoja y el archivo. Se confirmó la existencia de C+C como área antigua cerrada; se conserva inactiva. Las asignaciones concretas se marcan **Área asignada por correlación**: 19 a Capacitación, 4 a C+C, 3 a Galería, 3 a CEDOAL, 2 a CID y 1 a Sala. Los otros 28 casos no tienen una asignación suficiente con este criterio.

La clasificación inferida se muestra en HIL y trazabilidad junto al texto original, que no se reescribe. Las 32 filas conservan marca y exclusión; no se confunden con equivalencias institucionales confirmadas. No se crearon alias globales ni se fusionaron CEDOC y CEDOAL. Se mantienen 117 movimientos con marca y 8.367 elegibles. Hay respaldo restaurado, ensayo y 32 auditorías; [resultado con casos](outputs/revision-areas-historicas-20261028/Asignacion_areas_historicas.md) y [comprobación de solo lectura](backend/backups/revision_areas_historicas_20261028/verificacion_asignacion.json). Los siete nodos «Área: Ventas» se corrigieron posteriormente en C01, el 29/10.

### C01 completada: operaciones del catálogo, 29/10/2026

El clasificador distingue el tipo del catálogo en coincidencias exactas, alias y sugerencias; reserva «Área:» para departamentos y conserva la incertidumbre de los alias no confirmados. C+C continúa inactiva y disponible para interpretar el histórico. Las operaciones catalogadas con dirección incompatible requieren revisión.

Tras respaldo completo restaurado y ensayo se corrigieron siete filas de «Área: Ventas» a «Salida: Ventas», con estado `NO_APLICA` y siete auditorías. Se conservaron AREA escrita, originales, fechas, cantidades, saldos y las demás filas/tablas. Hay cero operaciones del catálogo etiquetadas como área. Pasaron 73 pruebas focalizadas y diez GET sobre PostgreSQL; permanecen los 117 tratamientos, 8.367 elegibles y 927 archivos privados. Los modelos y sus cortes congelados siguen consistentes; cuatro filas elegibles tendrán su nueva clasificación en un corte posterior, sin reentrenamiento automático. [Aplicación](backend/backups/c01_operaciones_catalogo_20261029/resultado.json) y [verificación](backend/backups/c01_operaciones_catalogo_20261029/verificacion.json).

### C02 implementada: selección de fuente documental, 29/10/2026

En Kárdex → Cobertura documental, Administrador/Auditor puede seleccionar la fila que acredita el cierre, abrir su foto y registrar el cotejo con referencia y motivo. Se conservan la evidencia, su huella y la autoría. La misma fuente se utiliza en inventario, apertura, libro digital, dashboard e informe institucional. Si cambia la evidencia o se importa una página antigua posteriormente, el cierre elegido se conserva y exige revisión; las aperturas utilizadas permanecen fijas.

La migración s94e53afb168 fue ensayada en una restauración y aplicada sin modificar datos existentes. Pasaron 331 pruebas backend (1 omitida), 86 frontend, la compilación y nueve GET con PostgreSQL. Permanecen 397 propuestas, cero confirmaciones, 38 bases bloqueadas y 8.367 elegibles. La aprobación institucional de fuentes y la cobertura física aún faltan. [Detalle y uso de C02](outputs/cierre-documental-20261029/Cierre_documental_C02.md).

### C03 implementada: áreas y catálogos, 29/10/2026

Desde Inicio → Áreas y catálogos se administran ubicaciones operativas, catálogo documental, alias y adscripción de cuentas, con historial consultable. Administrador escribe y Auditor consulta. Las bajas protegen stock, custodias y usuarios activos; el uso del área se serializa con la baja. Se conservan las identidades utilizadas y se rechazan versiones desactualizadas.

La migración t05f64b0c279 fue ensayada y aplicada sin cambiar datos previos: dos áreas registradas, solo Galería activa; Cedoal de baja; C+C histórica/inactiva. Siguen 64 alias, 32 inferencias y 28 avisos restantes, con 117 marcas HIL y 8.367 elegibles. Faltan validación institucional, adscripciones reales y matriz de permisos. [Uso y evidencia de C03](outputs/areas-catalogos-20261029/Administracion_areas_C03.md).

### C04 implementada: rectificaciones logísticas, 29/10/2026

Inventario actual permite rectificar transferencias, entregas externas y sus ventas/retornos con autorización de Administrador. Se conservan los datos originales y se añaden compensaciones vinculadas, con versión revisada, documento, motivo e idempotencia. Se controlan unidades disponibles, hechos posteriores, pendiente externo, áreas activas y cierre del periodo.

Libro, CSV, grafo, informe y balances anuales incorporan las compensaciones; una corrección posterior no altera el balance del corte anterior. La migración u16a75c1d380 se ensayó y aplicó sin modificar datos existentes. Los escenarios PostgreSQL se revirtieron en QA; siguen cero rectificaciones institucionales, 117 marcas HIL y 8.367 elegibles. C05 debe validar el circuito con personal y fuentes reales. [Uso y evidencia de C04](outputs/rectificaciones-logisticas-20261029/Rectificaciones_logisticas_C04.md).

### C05 preparada: inventario y circuito técnico, 29/10/2026

Inicio → Preparación del inventario permite consultar pendientes, abrir el artículo y preparar una ficha imprimible para el conteo. Administrador, Auditor y Operador pueden consultar; la ficha deja en blanco cantidades contadas, responsables y firmas, y no guarda ni aprueba existencias.

Las 26 unidades sin ubicación se desglosan en **20 de «PRUEBA E91159»**, cuya referencia también dice «PRUEBA», y **6 de «Testimonios de la literatura boliviana, vol. 2»**. La marca por nombre exige cotejo: no elimina ni excluye automáticamente cantidades. Las otras 6 son un saldo registrado, pendiente de conteo físico y ubicación; existe una operación posterior, por lo que corresponde conservar la apertura y documentar el ajuste que resulte, sin reiniciar mediante conciliación inicial. Solo Galería está activa.

El circuito conectado de 14 etapas se verificó en una base PostgreSQL aislada: conciliación, ingreso, venta, devolución, transferencia, entrega, venta/retorno externo y cuatro rectificaciones. También se probaron cierre, bloqueo de escrituras, reapertura y segunda versión del balance. No hay nueva migración en C05; continúa u16a75c1d380. Se conservan los registros institucionales y los 927 archivos privados. El conteo y la aceptación con personal, las actas y el cotejo documental siguen pendientes. [Guía, protocolo y resultados](outputs/preparacion-inventario-20261029/Preparacion_y_piloto_C05.md).

### C06 implementada: validación del proyecto, 29/10/2026

Inicio → Validación del proyecto separa concordancia documental y evaluación del detector. Administrador/Auditor prepara un estudio de hasta 100 filas, con población, selección reproducible, protocolo y fotos congelados mediante huellas. Otra cuenta realiza el cotejo; quien preparó el estudio o entrenó la versión no puede etiquetarla. Operador consulta. En esta pantalla se omiten predicción, puntuación y decisiones analíticas/HIL anteriores; la independencia profesional requiere comprobar el protocolo y los accesos externos.

Las etiquetas nuevas se conservan aparte, con autor, fecha, referencia, declaración de independencia, historial y control de versiones. La concordancia por fila o precisión/recall/F1 de la muestra se calculan únicamente al completar conclusiones válidas y conservar la evidencia. Los errores documentales y casos no concluyentes siguen pendientes; una división indefinida se mantiene sin porcentaje. Se exportan datos y etiquetas de la muestra, población de identificadores y huella verificable. La concordancia vigente no mide exactitud del OCR original ni acredita publicación institucional.

Pasaron 372 pruebas backend (una omitida en SQLite), 110 frontend y 160 en PostgreSQL sin omisiones, además de compilación, pantalla y cinco GET de solo lectura. Se conservan datos, modelos y 927 archivos privados, sin migración nueva. Hay cero estudios/etiquetas reales; las métricas humanas, el diseño temporal suficiente y la aprobación del dataset siguen pendientes. [Uso, protocolo y límites de C06](outputs/validacion-proyecto-20261029/Validacion_independiente_C06.md).

## Cómo funciona

| Apartado | Función disponible y condición de uso |
|---|---|
| Kárdex escaneados | Artículos, fotos ordenadas, extracción estructurada con Gemini, títulos, tandas, estado de carga y reintentos sin duplicación. |
| Human in the Loop | Foto y primera extracción conservadas; corrección vigente con motivo e historial. Distingue datos reconstruidos, discrepancias reales e incertidumbres. |
| Inventario actual | Toma una base documental utilizable o un conteo aprobado. La apertura conserva su fuente y no cambia silenciosamente por correcciones posteriores del histórico. |
| Entradas y salidas | Cantidad, tipo de operación, encargado interno, usuario registrador y receptor cuando corresponde; hora del hecho separada de la del registro. |
| Transferencias | Traslado atómico entre áreas activas con existencias suficientes en el origen. Requiere stock realmente ubicado. |
| Custodia externa | Feria o consignación conserva patrimonio institucional; la venta lo descuenta y el retorno recupera ubicación. |
| Devoluciones y ajustes | Vínculo con el movimiento original, límites de cantidad y asientos correctivos documentados, conservando los antecedentes. |
| Kárdex digital y grafo | Libro por artículo, saldos, integridad, CSV y trazabilidad con documentos y fotografías. El grafo no acredita por sí solo un recorrido físico. |
| Reportes y gestiones | Consulta y descarga de inventario y movimientos por período; informe institucional y cierres versionados con sus condiciones de aprobación. |
| Alertas y seguimiento | Reglas inmediatas y casos con evidencia, asignación, revisión y conclusión. Cerrar un caso no corrige el stock. |
| Analítica histórica | Nueva versión retrospectiva entrenada y verificada el 20/10 con el corte depurado actual; evaluación humana y calibración institucional pendientes. |
| Analítica digital | Modelo distinto para operaciones posteriores al corte, con horas y contexto verificables. Su preparación y activación requieren datos suficientes y revisión. |

### Entrenamiento histórico del 20/10/2026

Por instrucción del titular se entrenó la versión **`46e3683e-0210-4917-aadf-656af9dd2e2c`**, completada con 200 árboles, semilla 42 y porcentaje provisional de revisión del 5 %. El corte comprende 8.367 candidatos de 356 artículos, de 2005–2025. Los lotes y sus duplicados exactos se mantienen agrupados; las referencias estadísticas se ajustan exclusivamente con entrenamiento.

| Partición | Movimientos | Alertas |
|---|---:|---:|
| Entrenamiento | 5.030 | 165 |
| Calibración | 1.722 | 83 |
| Evaluación reservada | 1.615 | 111 |
| Total puntuado | 8.367 | 359 |

El umbral es **0,6115351601984308**; las 359 alertas incluyen entrenamiento y calibración, por lo que no deben presentarse como 359 hallazgos de evaluación independiente. Las 111 alertas reservadas requieren revisión humana. En evaluación, 1.376/1.615 filas carecen de referencia propia de artículo/dirección en entrenamiento y utilizan el respaldo global; esto limita la interpretación y debe acompañar la evaluación de utilidad. La estabilidad entre semillas no demuestra precisión ni fraude.

La integridad de resultados y la reproducción del artefacto quedaron **CONSISTENTES**. Solo cambiaron las tablas de versiones, resultados analíticos y auditoría; los movimientos, artículos, tratamientos HIL, la versión anterior y los 926 archivos privados preexistentes permanecieron intactos. Se conservan el [manifiesto del entrenamiento](backend/backups/entrenamiento_historico_20261020/manifiesto.json), [dataset candidato con particiones](backend/backups/entrenamiento_historico_20261020/dataset_candidato.jsonl), [diccionario](backend/backups/entrenamiento_historico_20261020/diccionario.json) y [evaluación técnica independiente](backend/backups/entrenamiento_historico_20261020/evaluacion_independiente.json). Son evidencias locales privadas; su preparación técnica no equivale a aprobación institucional.

Se mantuvieron excluidos los 40 artículos observados, sus 2.368 movimientos activos y los 116 casos HIL con marca. Esta versión es **retrospectiva**: el corte temporal para evaluar 2025 conserva solo 3 filas de calibración y 3 de evaluación después de purgar documentos que cruzan períodos. El modelo operativo digital continúa sin entrenamiento ni activación.

### Cuaderno de calibración experimental del 28/10/2026

El 28/10 se añadió un [notebook ejecutado de calibración experimental](outputs/calibracion-isolation-forest-20261028/Calibracion_Isolation_Forest.ipynb), su [informe con gráficos para presentar](outputs/calibracion-isolation-forest-20261028/Calibracion_Isolation_Forest.html) y un [paquete compatible con Colab](outputs/calibracion-isolation-forest-20261028/Paquete_calibracion_IF.zip). Reproduce las puntuaciones y el umbral del corte congelado; compara siete capacidades de revisión y doce combinaciones de árboles/semillas en entrenamiento/calibración. Muestra estabilidad, carga, distribuciones y cobertura de referencias, sin atribuirles precisión supervisada. Es un experimento local separado: no cambia el modelo ni sus revisiones humanas.

### Tres distinciones que deben mantenerse

- **Tanda** identifica la procedencia de la carga; **gestión** identifica el año del documento o de la operación. Una tanda no es una partición automática de entrenamiento.
- **Saldo documental** es lo escrito; **saldo calculado** es la reconstrucción; **stock operativo** es la base aprobada y sus eventos posteriores. Un conteo físico aporta evidencia adicional.
- **Aviso HIL**, **regla inmediata** y **rareza detectada por el modelo** tienen causas y revisiones diferentes. Una alerta no acredita fraude.

Los movimientos digitales de 2026 mantienen su origen y responsables al cambiar de año: no se convierten en fotografías históricas. Los cierres y nuevas versiones de modelos conservan períodos y trazabilidad.

### Controles inmediatos

El servidor bloquea cantidades inválidas y operaciones imposibles por stock. Las operaciones posibles pueden generar avisos por retiro total o mayoritario, magnitud extrema, repetición, demora o registro fuera del horario provisional **07:00–20:00, America/La_Paz**. Los umbrales son configurables y necesitan calibración institucional.

La auditoría histórica también dispone de reglas sobre documentos antiguos; las horas no escritas no se inventan para aplicarlas. Las reglas y límites de stock no dependen de que exista un modelo operativo activo.

## Roles y permisos

Hay **tres roles institucionales**, no niveles de suscripción:

| Rol | Alcance principal |
|---|---|
| Administrador | Cuentas, configuración autorizada, operaciones, conteos, conciliaciones, ajustes, modelos y cierres. |
| Operador | Artículos y escaneos, correcciones OCR con evidencia y registro de operaciones, transferencias, devoluciones y custodia. |
| Auditor | Consulta, reportes, validación de muestras y cobertura, revisión y conclusión de casos; sin registrar operaciones de stock ni corregir OCR. |

Los tres pueden consultar inventario, Kárdex y evidencias. El servidor comprueba cuenta y rol vigentes; la interfaz no sustituye la autorización. Fotografías, modelos y respaldos tienen acceso restringido. Los permisos por área y la independencia de revisiones sensibles siguen en el plan de continuidad.

## Operación técnica básica

Arquitectura: Vue 3/TypeScript en frontend; FastAPI, SQLAlchemy y Alembic en backend; PostgreSQL; Gemini para extracción e Isolation Forest con scikit-learn. Los secretos y la conexión se configuran en `.env` fuera de Git.

Entorno recomendado: Python 3.12 y Node 24; Node también admite 22.12 o posterior dentro de la versión 22. Las bibliotecas analíticas NumPy/scikit-learn conservan sus versiones para proteger la compatibilidad de los artefactos existentes. Para actualizar dependencias de una instalación existente, usar `python -m pip install -r requirements.txt` desde backend y `npm ci` desde frontend.

Para iniciar la instalación existente, con PostgreSQL y dependencias preparados, desde la raíz:

```powershell
.\iniciar-sistema.ps1
```

El [iniciador local](iniciar-sistema.ps1) usa los servicios de desarrollo y no inicializa la base. La interfaz se sirve en `http://localhost:5173/` y la API en `http://127.0.0.1:8000/`. Una instalación existente no debe recrearse para iniciarla.

El [script de respaldo y recuperación](backend/scripts/respaldo_recuperacion.py) genera y verifica copias coherentes. Desde backend:

```powershell
.\.venv\Scripts\python.exe -m scripts.respaldo_recuperacion
```

La restauración comprobable crea otra base y otra carpeta de recuperación; no sustituye por sí sola la instalación actual. Para una base nueva existen inicialización protegida y creación interactiva del primer Administrador. Su uso no forma parte del inicio cotidiano.

La implementación local y las pruebas previas no equivalen a aceptación institucional ni a certificación del despliegue público. La configuración final, recuperación del corte completo y piloto con el personal siguen documentados en los pendientes.

## Auditoría integral del 18/10/2026

Antes de cambiar el sistema se publicó el respaldo de código [respaldo/antes-auditoria-20261018](https://github.com/ElGorras1/proyecto_grado/tree/respaldo/antes-auditoria-20261018), commit `c5e9754`. Las mejoras se conservan en [auditoria/optimizacion-integral-20261018](https://github.com/ElGorras1/proyecto_grado/tree/auditoria/optimizacion-integral-20261018). La base, fotografías y modelos tienen respaldo local coherente y restaurado; no se publican en GitHub.

- Se corrigieron códigos de artículos repetidos por altas en el mismo segundo y la persistencia de artículos sin su auditoría. También se validan los nombres contra el tamaño real de la columna.
- El resumen de existencias respeta la apertura operativa y el cierre físico. Los contadores HIL y el grafo descartan filas anuladas o notas sin efecto; antes, 15 filas de esos estados podían sumar avisos en el catálogo.
- La revisión de una regla histórica consulta el artículo completo, conservando antecedentes de otras gestiones. Los listados omiten la cadena redundante de revisiones previas; la evidencia completa permanece en la base y en las auditorías.
- Se retiraron 30 archivos heredados sin uso, incluidas utilidades de borrado/cambios directos, un gráfico huérfano con sus cuatro pruebas, una pantalla administrativa de demostración y un esquema sin referencias. `/admin` conduce a la gestión real de usuarios. Se eliminaron dependencias sin uso y nueve importaciones innecesarias; los modelos necesarios para Alembic se conservaron.
- El archivo JavaScript principal bajó de aproximadamente 303 a 160 KB, sin cambiar los estilos ni los controles utilizados. Las auditorías de paquetes finalizaron sin vulnerabilidades conocidas reportadas: antes había 98 avisos Python y 10 paquetes afectados en npm.
- El importador mantiene exclusión entre procesos en Windows y Linux, sin reactivar cargas pausadas. Los fallos de catálogo quedan registrados sin exponer su contenido. Hay comprobación de conexión en `/health/ready`, límites de configuración válidos, JWT con sujeto y caducidad obligatorios, restricciones para claves/CORS en producción, contextos Docker que excluyen datos y secretos, servicios locales limitados a localhost y verificación automática en GitHub.

La base quedó en Alembic **`q72c31ed9f46`**, con dos índices nuevos para artículo/orden físico y lote. Se ensayaron aplicación, retirada y reaplicación sobre una restauración. Una consulta de cierre medida pasó de 5,329 a 0,047 ms; es una medición puntual, no una garantía de tiempo para todos los informes.

Se conservaron los contenidos de las 43 tablas de negocio y todas las secuencias; solo cambió el registro de versión de Alembic. Se verificaron **926 archivos privados**, cero referencias huérfanas, cero posiciones históricas activas duplicadas y las dos distribuciones operativas existentes. Los 8.367 elegibles y los 116 tratamientos con marca permanecen iguales; esta auditoría no entrenó modelos ni modificó movimientos.

Resultado de comprobaciones: **274 pruebas backend aprobadas, una omitida; 79 frontend; 101 del piloto PostgreSQL aislado; 66 consultas reales con respuesta esperada**, compilación y análisis estático sin errores. Las cuatro pruebas frontend retiradas pertenecían exclusivamente al componente huérfano. Persisten avisos de formato de Vue y una advertencia de compatibilidad futura del cliente de pruebas HTTP; no hubo fallos funcionales asociados.

Los resultados detallados y el código retirado están en [el respaldo técnico de la auditoría](backend/backups/auditoria_integral_20261018/); el respaldo completo previo, en `backend/backups/respaldo_20261019T030623556491Z/` — fecha UTC, todavía 18/10 en Bolivia. Docker Compose se validó sintácticamente; no se certificó un despliegue público ni una prueba de carga concurrente.

Para repetir el diagnóstico sin escribir en las tablas:

```powershell
.\.venv\Scripts\python.exe -m scripts.auditar_sistema --salida backups/auditoria_actual.json
```

## Conservación de la documentación anterior

Los informes por lote, HTML, índices y documentos sustituidos se retiraron de `docs/` después de verificar su respaldo. Se conservan **132 archivos anteriores**, incluido el README previo, en un único [archivo histórico comprimido](backend/backups/documentacion_consolidada_20261018/documentacion_anterior.zip), con [manifiesto SHA256](backend/backups/documentacion_consolidada_20261018/manifiesto_originales.json).

Los archivos técnicos de evidencia permanecen accesibles en el respaldo, y las fotos, planes HIL y auditorías mantienen sus ubicaciones operativas. El ZIP y esos respaldos son locales y están fuera de Git; deben acompañar una entrega institucional que los necesite. El Excel histórico del 12/10 citado anteriormente no se encontró en su ruta de entrega y no se presenta como dataset actual.

**Regla de mantenimiento:** actualizar estos tres documentos. Los resultados detallados de nuevas ejecuciones van a sus respaldos técnicos; no crear otro documento de avance por cada lote ni reintroducir índices históricos en `docs/`.
