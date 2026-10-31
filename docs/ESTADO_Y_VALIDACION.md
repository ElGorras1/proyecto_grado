# Estado, pruebas y pendientes

## Auditoría funcional y retiro autorizado del registro de ensayo

Comprobación posterior del 31/10/2026 sobre el código 79e1dc7. El núcleo funcional
está implementado y las verificaciones realizadas no reprodujeron un fallo central.
La entrega institucional todavía requiere cerrar los datos y su evaluación.

- Servidor: 410 pruebas aprobadas y cuatro omitidas en SQLite por requerir PostgreSQL.
- PostgreSQL aislado: 201 aprobadas, sin omisiones; circuito de 14 etapas y preservación
  de tablas, secuencias y 927 archivos institucionales antes de la limpieza autorizada.
- Interfaz: 116 aprobadas, análisis estático, tipos y compilación correctos.
- Consultas con datos actuales: 49 respuestas esperadas por los tres roles, antes y
  después de la limpieza. La identidad se sustituye solo en el cliente de ensayo
  y la conexión utiliza una transacción de solo lectura; no acredita un login real.
- API y conexión a PostgreSQL responden; la interfaz local quedó iniciada. Los recursos
  protegidos rechazan la consulta anónima. No había entrenamientos en cola.
- Gemini devolvió las dos filas, fechas y cantidades esperadas de una tarjeta ficticia.
  Esta comprobación no incorporó documentos ni movimientos a la base institucional.

El titular confirmó que **PRUEBA E91159** era un ensayo y autorizó borrarlo. Tras un
respaldo completo restaurado y verificado, se retiraron exclusivamente el artículo 1,
sus nueve movimientos digitales y su apertura de 20 unidades. La acción conserva
auditoría y snapshot; los demás registros y los 927 archivos privados se verificaron
intactos. El expediente está en outputs/auditoria_cierre_funcional_20261031/.

El corte posterior tiene **398 artículos, 11.909 movimientos, una apertura y seis
unidades sin ubicación**. No quedan artículos con indicio de prueba en el listado de
preparación. Persisten 38 bases bloqueadas, 397 fuentes sin confirmación documental,
una sola área activa y cero estudios o etiquetas institucionales independientes.
Las transferencias requieren dos áreas activas: el circuito está probado en QA,
pero esta instalación todavía no cumple esa condición de operación.

Prioridades para cerrar la entrega: verificar las seis unidades y su ubicación;
confirmar áreas y fuentes con la institución; ejecutar la evaluación independiente
del detector y el cotejo del grafo; fijar el alcance del modelo operativo digital,
que sigue sin entrenamiento por datos insuficientes. Docker continúa aplazado.
Los recuentos inferiores corresponden a cortes previos y se conservan como historia.

## Cierre metodológico del 31 de octubre

La herramienta de estudios nuevos se alineó con el capítulo I: NORMAL, ANOMALO e
INDETERMINADO; criterio documental obligatorio para anomalías; segunda revisión
registrada para excluir indeterminados persistentes; muestra y denominadores
explícitos. Conserva sin reinterpretar los estudios versión 1. Admite hasta 5.000
filas y rechaza superar el marco, sin reducir silenciosamente la muestra.
La consulta de lectura cuenta 11.859 movimientos documentales con ruta de foto:
la recomendación técnica se recalcula a 373, pendiente de confirmación institucional.

La auditoría del corte del 20/10 encontró seis artículos entre conjuntos, sin lotes
ni fotos cruzados. La nueva opción POR_ARTICULO mantiene esos componentes juntos.
El experimento separado del 31/10 tiene 4.689/2.169/1.509 filas y 214/71/71 artículos,
cero cruces, umbral 0,6075246749034304 y 60 alertas de evaluación. Las 1.509 filas
reservadas utilizan referencia global: es generalización a artículos no vistos,
no superioridad ni validación temporal. No se registró el modelo experimental en
la instalación ni se sustituyó la versión del 20/10, cuya reproducción sigue CONSISTENTE.

Pruebas actuales: 410 aprobadas y 4 omitidas en servidor SQLite; 116 aprobadas en
interfaz, con tipos y compilación correctos; 201 en PostgreSQL aislado, sin omisiones.
No sumar conjuntos solapados. El circuito PostgreSQL conserva tablas, secuencias y
927 archivos institucionales. Son ensayos técnicos, no un piloto con personal.

Las capturas nuevas de validación utilizan la interfaz compilada con respuestas
sintéticas, identificadas como QA: no crearon estudios ni etiquetas institucionales.
La ejecución Docker continúa pospuesta; su trabajo CI requiere una solicitud manual
explícita y no se inicia con cada publicación. Las métricas humanas, los conteos,
la aceptación y el diseño temporal suficiente siguen pendientes. El protocolo
está en [PROTOCOLO_EVALUACION.md](PROTOCOLO_EVALUACION.md); los expedientes privados
del cierre permanecen en outputs/cierre_capitulo_III_20261031_v2/.

Los apartados siguientes conservan el corte anterior del 30/10 y sus antecedentes.

Actualización técnica: 30/10/2026, Bolivia. Pruebas, dependencias, recuperación e
integridad comprobadas durante esta revisión; las carpetas con fecha UTC 31/10
corresponden a la noche del 30/10 en Bolivia. El cotejo institucional de documentos
y existencias sigue pendiente. [Inicio](../README.md) · [Manual](MANUAL_SISTEMA.md).

## Estado general

El núcleo funcional está implementado y comprobado técnicamente. La aceptación con
personal, las confirmaciones documentales, el dataset oficial, la evaluación humana
del detector y la entrega de producción siguen pendientes.

| Bloque | Situación vigente |
|---|---|
| N01: fechas documentales | Fechas completas, parciales, ausentes e ilegibles representadas sin completar datos supuestos; fuente y primera lectura conservadas. |
| C01: clasificación de operaciones | Corregido el tipo de catálogo y siete nodos «Área: Ventas», con auditoría. |
| C02: fuente de cierre | Selección de fila/foto implementada; cotejo y cobertura institucional pendientes. |
| C03: áreas y catálogos | Administración y adscripción implementadas; validación institucional de áreas, personas y equivalencias pendiente. |
| C04: rectificaciones logísticas | Transferencias, entregas y ventas/retornos corregibles mediante compensaciones; aceptación real pendiente. |
| C05: inventario y piloto | Fichas de preparación y circuito QA de 14 etapas comprobados; conteos, ubicación y aceptación con personal pendientes. |
| C06: validación independiente | Estudios, etiquetas separadas y exportación implementados; hay cero estudios y etiquetas reales. |
| C07: entrega reproducible | Avance técnico verificado: dependencias fijadas, entorno limpio, permisos de base y recuperación. Pila de producción preparada; construcción/arranque en Docker, HTTPS y carga pendientes. |
| Interfaz | Mosaico uniforme aplicado el 30/10, con herramientas y permisos conservados. |
| Revisión funcional adicional | Corregidos guardado conjunto de cuentas/auditoría, roles inutilizables, correos duplicados por mayúsculas, validaciones de usuario, sesiones nuevas tras restablecer contraseña, errores de OCR y protección CSV. Sin cambios de datos institucionales. |

## Datos y calidad documental

| Indicador del corte | Resultado |
|---|---:|
| Artículos registrados | 399 |
| Movimientos conservados | 11.918 |
| Históricos / históricos activos | 11.908 / 11.859 |
| Registros digitales sin lote histórico | 10 |
| Movimientos elegibles / artículos representados | 8.367 / 356 |
| Gestiones elegibles | 2005–2025 |
| Casos HIL tratados | 400 |
| Sin avisos / con marca / sin categorizar | 283 / 117 / 0 |
| Artículos observados excluidos del entrenamiento histórico | 40 |
| Rutas históricas de fotos presentes / faltantes | 693 / 0 |
| Huérfanos / posiciones históricas activas duplicadas | 0 / 0 |
| Archivos privados verificados | 927 |

Las tres tandas previstas se incorporaron; la cobertura de todo el archivo físico
requiere certificación institucional. Comprobar presencia de fotos no equivale a
leer nuevamente cada celda. Los elegibles superan controles actuales; las marcas
HIL permanecen fuera de la selección y no se presentan como datos confirmados.

**Áreas históricas:** de 60 marcas, 32 tienen asignación inferida: Capacitación 19,
C+C 4, Galería 3, CEDOAL 3, CID 2 y Sala 1. Las otras 28 son 13 equivalencias sin
confirmar, 8 lecturas inciertas, 6 marcas del papel y 1 efecto indeterminado. Las 32
inferencias conservan aviso y exclusión. Hay 64 alias: 23 con bandera previa de
confirmación y 41 sugeridos; esa bandera por sí sola no acredita aprobación institucional.

**Cierres:** 397 propuestas, cero confirmaciones documentales, 359 bases que pasan
controles y 38 bloqueadas: 24 por alertas matemáticas, 13 por fecha incompleta/técnica
y 1 por saldo fuera de rango. Fuente utilizable y fuente cotejada son estados distintos.

**Operación real pendiente:** dos aperturas y 26 unidades sin ubicación: 20 de
«PRUEBA E91159», cuya condición debe aclararse, y 6 de «Testimonios de la literatura
boliviana, vol. 2». Estas últimas son saldo registrado, pendiente de conteo. Su base
histórica es 8 y existe una operación posterior; conservar apertura y operación y
documentar el ajuste que resulte. Solo Galería está activa; Cedoal está de baja y
C+C es histórica/inactiva. Las pruebas QA no acreditan transferencias, custodias,
rectificaciones o cierres institucionales reales. La gestión 2026 continúa abierta.

## Isolation Forest y calibración

La versión histórica retrospectiva `46e3683e-0210-4917-aadf-656af9dd2e2c`, entrenada
el 20/10, utiliza 200 árboles, semilla 42 y umbral `0,6115351601984308`, con capacidad
provisional de revisión del 5 %. Las referencias estadísticas se ajustan con
entrenamiento y los documentos/duplicados se mantienen agrupados.

| Partición | Movimientos | Alertas |
|---|---:|---:|
| Entrenamiento | 5.030 | 165 |
| Calibración | 1.722 | 83 |
| Evaluación reservada | 1.615 | 111 |

Las 359 alertas del conjunto incluyen entrenamiento y calibración; la evaluación
reservada tiene 111. En ella, 1.376 filas utilizan referencia global por falta de una
referencia propia de artículo/dirección. Reservar temporalmente 2025 deja solo 3 filas
de calibración y 3 de evaluación tras la purga documental: el diseño temporal requiere
mejorarse. No hay etiquetas humanas independientes ni precisión, recall o F1 acreditados.

El cuaderno del 28/10 reproduce el corte congelado y compara siete umbrales de revisión
y doce combinaciones de árboles/semillas usando entrenamiento/calibración. Estabilidad,
Jaccard, Spearman, carga y coincidencia con reglas no sustituyen métricas supervisadas.
Los experimentos no activan versiones nuevas ni cambian HIL.

El modelo de operaciones digitales es independiente: permanece sin entrenamiento ni
activación, con 1 evento elegible frente al mínimo de 125 y 14 días. Las reglas de
stock y alertas inmediatas sí funcionan. No se completa esa población con OCR o
operaciones ficticias.

## Pruebas y límites conocidos

| Verificación | Resultado y fecha |
|---|---|
| Suite general del servidor | 403 aprobadas y 4 omitidas por requerir PostgreSQL, con Python 3.11 local; 30/10. Las omisiones incluyen las dos pruebas de solicitudes simultáneas y se ejecutan en el piloto PostgreSQL. |
| Interfaz | 112 aprobadas; análisis estático y compilación correctos; 30/10. Incluye adjuntos operativos en la ficha. La administración carga todas las páginas de usuarios. |
| Piloto PostgreSQL aislado | 194 aprobadas, sin omisiones, con circuito de 14 etapas; 30/10. Incluye migración y permisos de adjuntos, correcciones funcionales y dos solicitudes simultáneas con conexiones independientes: sin sobregiro y sin duplicación del mismo envío. No sumar a la suite general: cubre pruebas solapadas. |
| Revisión del rediseño con datos reales | 28 comprobaciones: tres roles, inicio/inventario/ficha/Kárdex/accesos y anchos 1440, 768, 390 y 320; 30/10. Cero errores JS/API, desbordamientos de página o escrituras. |
| Conservación de lógica de interfaz | 154 enlaces originales de formularios/acciones conservados entre ficha y catálogo histórico; 30/10. |
| Base y recuperación | Respaldo previo restaurado y reconciliado; ampliación de adjuntos aplicada `v27b86d2e491`; 30/10. |
| Integridad durante las correcciones | Las tablas de negocio previas, sus secuencias y 927 archivos privados conservan sus huellas. El esquema ahora tiene 46 tablas: se añadió `documento_operativo` vacío y avanzó la versión Alembic; 30/10. |
| Instalación nueva y modelos | Entorno limpio Python 3.12 instalado desde el lock con hashes, `pip check` correcto y tres artefactos joblib existentes cargados sin reentrenar; 30/10. |
| Producción y automatización | Configuración Compose y estructura del flujo CI comprobadas. El motor Docker local no inició: la construcción y el arranque de contenedores no se acreditan. Las nuevas tareas CI aún no se han ejecutado en GitHub. |

La revisión funcional reprodujo fallos de cuentas/auditoría, validación de roles y
correos, protección de CSV y errores del lector externo; sus regresiones se
comprobaron en bases aisladas. Los cambios de contraseña de sesiones nuevas
invalidan tanto el acceso Bearer como la cookie de fotografías. El análisis de
las 115 operaciones documentadas solo encontró sin requisito Bearer los inicios
y cierres de sesión y las dos comprobaciones de salud; las fotografías tienen
validación propia. Esto complementa las pruebas de permisos, no sustituye una
auditoría de seguridad independiente.

La auditoría Python inicial del 30/10 reportó 30 avisos en seis paquetes. Se
actualizaron certifi, dnspython, filelock, pyasn1, pypdf y setuptools; las auditorías
posteriores del entorno local y del entorno limpio no reportan vulnerabilidades
conocidas. Las versiones del modelo entrenado se conservaron. Se corrigieron
además la conexión con contraseñas especiales, su interpolación en Alembic y la
localización de herramientas de respaldo en Windows/Linux.

En la interfaz se actualizó follow-redirects a 1.16.2. `npm audit --omit=dev` no
reporta avisos; el análisis completo conserva 18 entradas moderadas propagadas
desde dos dependencias de herramientas de desarrollo: glob y minimatch. Sus
correcciones disponibles cambian versiones mayores respecto de los rangos de
los consumidores instalados; no se impusieron sustituciones incompatibles. Debe
verificarse una actualización coordinada de esas herramientas antes de cerrar
C07. No quedan avisos altos ni críticos en el análisis actual. Fuentes:
[minimatch](https://github.com/advisories/GHSA-g3hv-75wg-m249) y
[glob](https://github.com/advisories/GHSA-3g3m-2fjr-6pw4). Estas auditorías no prueban
por sí solas la explotabilidad del sistema ni la ausencia de otras fallas.

Medianas locales del 29/10, con tres lecturas ASGI/PostgreSQL y sin concurrencia:
catálogo 2,769 s; perfil analítico 4,255 s; informe institucional 5,737 s. No son una
prueba de carga ni tiempos de extremo a extremo. En esta revisión se evitó leer el
JSON original de extracción en consultas que solo necesitan campos vigentes;
las respuestas de catálogo, corte analítico e informe institucional conservaron
sus huellas. La medición local tuvo una pausa prolongada y no se utiliza como
nuevo indicador de rendimiento. Los catálogos siguen mostrando todos sus artículos;
la paginación y simplificación de analítica pueden mejorar el uso.

## Orden para terminar

1. **Fuentes y áreas:** cotejar cierres/cobertura; resolver o justificar bloqueos,
   inferencias y siglas; aprobar áreas, participantes y alcance de permisos.
2. **Inventario real C05:** aclarar el artículo de prueba, contar y ubicar existencias,
   adjuntar referencias/actas y aceptar el circuito con personal autorizado.
3. **Evaluación C06:** aprobar protocolo, realizar cotejo y etiquetas independientes,
   medir resultados y mejorar el diseño temporal. La calidad del OCR original y
   la evaluación académica del grafo requieren mediciones específicas si el alcance las exige.
4. **Dataset y expediente:** cerrar versión, diccionario, exclusiones, procedencia y
   huellas; obtener aprobación institucional y preparar conclusiones de la defensa.
5. **Modelo operativo:** entrenar y evaluar cuando existan suficientes eventos reales
   y representativos, si forma parte del alcance acordado.
6. **Entrega técnica C07:** resolver los avisos restantes de herramientas de desarrollo
   mediante versiones compatibles y ejecutar la nueva verificación CI. Docker queda
   pospuesto por decisión del usuario. Para la entrega definitiva siguen pendientes
   despliegue, HTTPS, red, carga con varios usuarios, recuperación en el servidor
   definitivo y copia externa. Las pruebas de dos solicitudes simultáneas no sustituyen
   una prueba de carga.

**Documentos operativos:** ya se pueden cargar y descargar actas/facturas privadas
por artículo y referencia, con permisos, auditoría y comprobación de integridad.
Se incorporaron pruebas de acceso, archivo alterado y reversión por fallo de auditoría.
La paginación y el rendimiento de listados grandes, y la revocación individual de
sesiones copiadas, son mejoras técnicas diferenciadas de la validación institucional.
Las sesiones nuevas quedan invalidadas al restablecer su contraseña; las anteriores
a esta actualización mantienen su vencimiento original.

Se mantienen como mejoras sujetas a necesidad: préstamo a exposición, recepción de
transferencias en dos pasos, reposición, importación CSV/Excel, notificaciones y
operación sin conexión. No se convierten automáticamente en requisitos de cierre.

## Evidencia y mantenimiento

Las huellas, planes, resultados y respaldos permanecen en `backend/backups/`;
fotos y modelos conservan sus carpetas privadas. La verificación del rediseño está
en `backend/backups/rediseno_mosaico_20261030/`. Los originales sustituidos en esta
consolidación se guardan en `backend/backups/documentacion_consolidada_20261030/`,
con ZIP y manifiesto SHA-256; también se conserva el archivo histórico del 18/10.
Estos respaldos y los materiales de `outputs/` son locales y no se publican en Git.

La evidencia de estas correcciones está en
`backend/backups/c07_entrega_tecnica_20261030/`; el piloto final se conserva en
`backend/backups/piloto_20261031T002302756524Z/` y el respaldo restaurado en
`backend/backups/respaldo_20261031T002431177314Z/`. Los entornos y paquetes previos
se conservaron para permitir una reversión de dependencias.

La revisión funcional adicional se conserva en
`backend/backups/revision_funcional_20261030/`; su piloto final está en
`backend/backups/piloto_20261031T021340786759Z/`. Incluye las regresiones previas,
resultados finales, revisión de rutas y comparación de integridad.

La ampliación final de adjuntos está verificada en el piloto
`backend/backups/piloto_20261031T023512482624Z/`. Las pruebas generales, de interfaz,
compilación, respaldo y comparación antes/después de la migración están en
`backend/backups/revision_funcional_20261030/` (archivos con sufijo `adjuntos`).
La consulta autenticada en la base actual devolvió la lista vacía y la solicitud
anónima fue rechazada. No se cargaron actas ficticias en la instalación real.

**Versión funcional para el capítulo III:** describir los módulos implementados,
los documentos privados por artículo/referencia, las reglas, el detector histórico,
sus pruebas y sus límites. Las firmas, conteos, confirmaciones y métricas humanas
pendientes se presentan como validación futura; no como funciones inexistentes ni
resultados ya obtenidos. El modelo operativo continúa condicionado a eventos reales.

Actualizar los tres documentos principales y los dos materiales de calibración
cuando corresponda. Guardar resultados detallados en sus expedientes técnicos y
evitar nuevos informes narrativos de avance que dupliquen este resumen.
