# Manual del sistema

Fundación Simón I. Patiño · Actualizado el 31/10/2026.
[Inicio](../README.md) · [Estado, pruebas y pendientes](ESTADO_Y_VALIDACION.md).

## Propósito y componentes

El sistema conserva Kárdex escaneados, permite revisar su transcripción y conecta el
histórico con el inventario operativo, sus documentos y la auditoría. Usa Vue 3 y
TypeScript, FastAPI, SQLAlchemy/Alembic y PostgreSQL. Gemini realiza la extracción
documental; Isolation Forest apoya la selección de movimientos para revisión.

El alcance de datos institucionales del proyecto llega hasta **2025**. Esta es la
última gestión de referencia documental, aunque la aplicación se ejecute después.
Las fechas de los documentos y las fechas de registro se conservan por separado;
no se cambia el reloj ni se vuelven a ingresar los históricos como operaciones
actuales. El trabajo cotidiano se inicia en Revisiones y alertas: elegir un aviso
y abrir su evidencia. El sistema utiliza la referencia configurada sin exigir que
el personal seleccione versiones. En Consulta del análisis histórico se puede
filtrar el corte conservado por gestión y artículo. Consultar no entrena un modelo
nuevo ni confirma una irregularidad.

Al desplegar la cobertura de todas las gestiones se muestran disponibles, elegibles,
puntuados, alertas y no elegibles de cada año del corte. «Ver gestión» abre su
consulta. «Artículo del corte» selecciona una identidad exacta; la búsqueda de
texto sigue disponible al consultar todos los artículos. Un artículo sin elegibles
conserva su advertencia y requiere revisar las exclusiones, no se da por normal.

En Reportes, la consulta inicial utiliza Kárdex escaneado y su última gestión
disponible hasta 2025. Se puede seleccionar otra gestión u origen y pulsar
«Aplicar filtros». Si se edita sin aplicar, la tabla y su descarga conservan la
consulta anterior y muestran un aviso. El informe institucional comienza en 2025,
conservando por separado saldos actuales, documentos históricos y registros digitales.

En Resumen, «Imprimir o guardar PDF» incluye todos los artículos y eventos de la
consulta, aunque en pantalla se muestren en páginas de 30. La impresión repite los
encabezados de las tablas e indica cuándo se generó el informe y qué gestión
documental se consultó. Después de imprimir se conserva la página de pantalla.
En Balance/cierre, el historial de cierres sigue paginado; si hay varias páginas,
un aviso indica qué parte se incluye en la impresión. Cada cierre conserva además
su propia descarga completa en JSON.

Al aplicar otros filtros en Revisiones y alertas se cierra la evidencia anterior.
Un guardado pendiente no sustituye el detalle de otro aviso abierto después. Si
se resuelve el último aviso de una página y esta deja de existir, la bandeja vuelve
a la última página disponible.

En Analítica histórica, «Descargar auditoría filtrada CSV» incluye todas las
filas de la consulta aplicada, aunque ocupen varias páginas. Antes de descargar,
aplicar cualquier cambio de filtros. El archivo conserva versión, huella, umbral,
puntuación, partición, revisión y fuente del corte; no certifica discrepancias ni
adopta silenciosamente correcciones posteriores. Desde «Ver evidencia» se puede
abrir HIL o el grafo del mismo artículo. Las correcciones documentales y las
conclusiones del hallazgo se registran en sus respectivos formularios.

El corte del modelo cuenta 216 documentos de 2025; el reporte vigente cuenta 215
con año asignable porque una fila fue marcada después como fecha estimada. Los
188 resultados puntuados y los cuatro avisos de 2025 se mantienen en el modelo.

## Herramientas y permisos

| Espacio de trabajo | Uso principal |
|---|---|
| Artículos e inventario | Kárdex, fotografías, HIL, cobertura, grafo y operaciones. Al cambiar entre Kárdex y operaciones se conserva el artículo seleccionado. Preparación del conteo aparece en Más herramientas. |
| Revisiones y alertas | Bandeja de pendientes con origen documental, modelo o control operativo. Cada aviso abre su evidencia y su formulario correspondiente. Los avisos HIL ya categorizados se incluyen solo al solicitarlo. |
| Reportes | Movimientos filtrados y CSV para Excel, resumen institucional imprimible/PDF y balance/cierre por separado. Se conserva la gestión al cambiar de apartado. JSON queda como exportación avanzada. |
| Administración | Usuarios, áreas, accesos y mantenimiento del análisis. Los parámetros del modelo, estudios de validación y modelo digital están dentro de Herramientas avanzadas. |

El inicio presenta cuatro espacios para Administrador/Auditor y tres para Operador.
Los permisos de las funciones se conservan aunque cambie su ubicación. Los tres consultan
inventario, Kárdex y evidencia. Administrador gestiona cuentas y autoriza aperturas,
ajustes, rectificaciones y cierres. Operador registra operaciones y corrige lecturas
documentales con evidencia. Auditor revisa cobertura, estudios y casos; consulta
áreas y accesos, sin registrar movimientos de stock ni corregir OCR. Gestión de
usuarios es exclusiva de Administrador; Áreas y catálogos y Registro de accesos se
reservan a Administrador/Auditor. El servidor verifica los permisos en cada solicitud.

La adscripción de una cuenta identifica su área; el acceso operativo sigue regido
por rol. Una separación institucional adicional por área requiere definición y pruebas.

### Análisis y mantenimiento automáticos

El servidor comprueba cada cinco minutos los movimientos históricos nuevos o
modificados que superan los controles y pertenecen al alcance hasta 2025. Aplica
el modelo de referencia conservado; no vuelve a ajustarlo para obtener cada
puntuación. Las inferencias nuevas quedan en seguimiento separado, con fotografía,
valores, huella, versión y revisión propia. Los resultados del corte de evaluación
no se reemplazan. Un aviso requiere cotejo; una puntuación no confirma una discrepancia.

Cada treinta días comprueba si cambiaron los datos relevantes para entrenamiento.
Sin cambios no prepara otra versión. Cuando existen cambios y hay grupos y filas
suficientes, prepara automáticamente un candidato con separación por artículo.
Se conserva el modelo en uso mientras se comprueba la versión candidata. Seleccionar
otra referencia es mantenimiento avanzado, exige motivo y comprobaciones técnicas;
la consistencia técnica no acredita por sí sola una mejora de precisión.

El personal consulta Revisiones y alertas y documenta el cotejo. No necesita
solicitar entrenamientos ni elegir parámetros. Administración → Mantenimiento del
análisis permite consultar el último intento, errores y próxima revisión. Solo
Administrador modifica la configuración; Auditor puede consultarla. Una
configuración desactualizada no sobrescribe cambios de otra persona.

Las tareas funcionan mientras el servidor está iniciado. Tras una interrupción,
las comprobaciones vencidas se retoman al arrancar. Si falla el modelo o su archivo
no coincide con la huella conservada, no se publican nuevas puntuaciones y se muestra
el problema en mantenimiento. Pausar la programación no modifica el archivo ni sus datos.

Crear, editar, desactivar, reactivar o restablecer la contraseña guarda el cambio y
su auditoría en una misma transacción. Si la auditoría falla, el cambio se revierte.
Solo se habilitan cuentas con uno de los tres roles activos admitidos. Los correos
se comparan sin distinguir mayúsculas para iniciar sesión y evitar duplicados;
las cuentas existentes no se reescribieron. Los nombres no pueden estar vacíos y
el correo debe caber en su columna de almacenamiento.

Los nuevos inicios de sesión vinculan el token a la contraseña vigente mediante
una huella que no expone el hash almacenado. Restablecer la contraseña invalida
esas sesiones y sus cookies de fotografías. Los tokens emitidos antes de esta
actualización conservan su vencimiento original (60 minutos con la configuración
local por defecto). Salir borra la sesión del navegador y la cookie; no es una
lista de revocación individual de tokens copiados a otro dispositivo.

## Digitalización, HIL y áreas históricas

1. Crear o seleccionar el artículo y cargar sus fotografías. Revisar título, orden,
   páginas y estado de la tanda; los reintentos mantienen controles de duplicación.
2. Consultar el historial y abrir Auditoría HIL. Cotejar el dato con la foto y registrar
   decisión y motivo. Se conservan primera extracción, valor vigente y auditoría.
3. Corregir lecturas acreditadas. Cuando el papel contiene una discrepancia real,
   conservarla y mostrar el cálculo por separado; una hipótesis conserva su marca.
4. Representar blancos, fechas parciales o ilegibles sin convertirlos en cero ni
   completar una fecha supuesta. Las operaciones digitales sí exigen fecha del hecho.
5. Revisar una decisión si cambió su evidencia. Categorizar un aviso documenta el
   problema; las exclusiones analíticas solo cambian con una decisión justificada.

Una **tanda** identifica la carga; una **gestión**, el año documental u operativo.
Saldo escrito, saldo reconstruido, stock operativo y conteo físico son valores
distintos. Avisos HIL, reglas inmediatas y rareza del modelo también tienen revisiones
distintas. Concluir un caso de alerta no corrige existencias.

El 31/10 el titular identificó como ensayo la salida 12277 de «TESTIMONIOS DE LA
LITERATURA BOLIVIANA VOL. 2». Se retiró junto con su apertura automática, conservando
artículo, documentos y auditoría. Su saldo de ocho unidades vuelve a mostrarse
como base documental sin apertura operativa; no acredita existencias físicas
actuales. La instalación queda sin movimientos digitales ni aperturas, y la
analítica operativa no dispone de eventos para entrenar. El detector histórico
conserva sus puntuaciones y funciona independientemente de esa capacidad futura.

Si falla el servicio de lectura, la respuesta no reproduce errores internos del
proveedor y permite reintentar el mismo lote. Un intento propio marcado FALLIDO
retira únicamente las copias temporales creadas por esa solicitud; no se eliminan
fotografías preexistentes, lotes confirmados ni extracciones pendientes. Los archivos
nuevos se crean sin sobrescribir otros. Las exportaciones CSV neutralizan también
los textos que comienzan con espacios antes de una fórmula, conservando el original
en la base.

Las áreas inferidas se asignaron por parecido y frecuencias de artículo, hoja y
archivo; su soporte es heurístico, no una probabilidad validada. Se conserva la sigla
literal y la condición inferida. C+C conserva su marca histórica/inactiva en el catálogo documental; CEDOC y CEDOAL conservan
identidades separadas. Confirmar un alias exige cotejo y motivo; no confirma las filas
previas. Desactivarlo impide nuevas asignaciones por esa lectura.

Por indicación del titular están habilitadas las 11 áreas conocidas como ubicaciones
operativas, incluida C+C para el alcance hasta 2025. Se conservaron los identificadores
de CEDOAL y Galería, y se añadieron las otras nueve. La habilitación no confirma
equivalencias del archivo ni asigna existencias. La pantalla informa disponibilidad
de transferencias y advierte dependencias incompatibles con una baja.

Decisiones que deben conservarse al continuar la revisión:

| Caso | Tratamiento |
|---|---|
| Campero | Cierre escrito 300 y cálculo condicional 309; conservar discrepancia, exclusión y bloqueo. |
| POLIGENESIS y REV DE HISTORIA POLIGENESIS 1 | Artículos separados por decisión del titular aunque compartan fotos. |
| Criterio T13 | Cuatro ingresos confirmados: 1, 2, 1 y 4. |
| Movimiento 12272 | Fecha documental ausente; primera lectura técnica conservada y valor vigente sin fecha. |
| Operaciones parecidas, cifras tapadas y notas marginales | Conservar procedencia e incertidumbre; resolver con evidencia del caso. |

## Fuente documental e inventario

En **Kárdex → artículo → Cobertura documental**, Administrador/Auditor selecciona la
fila de cierre, abre la foto, coteja orden, fecha y saldo y registra referencia y
motivo. Se conserva la huella de la evidencia. Ante cambios, actualizar y revisar;
una fuente desactualizada bloquea nuevas aperturas históricas. La base de una apertura
ya utilizada se mantiene fija. Confirmar el cierre tampoco certifica cobertura total
del archivo o un conteo físico.

En **Inventario actual → artículo**, el índice permite localizar las secciones:

- **Apertura y conciliación:** utilizar una base documental operable o un conteo
  autorizado con respaldo. La conciliación inicial tiene condiciones propias;
  después de operaciones posteriores puede corresponder un ajuste documentado.
- **Existencias y transferencias:** asignar cantidades físicamente verificadas con
  área, encargado, documento y motivo. Transferir requiere dos áreas activas y
  disponibilidad en origen; conserva el total institucional.
- **Ingresos, salidas y devoluciones:** registrar tipo, cantidad, participantes y
  documento. Se separan hora del hecho y del registro; una devolución se vincula a
  la entrega original y respeta el pendiente.
- **Custodia externa:** una feria o consignación conserva el patrimonio; la venta
  lo descuenta y el retorno recupera ubicación. No se puede superar el pendiente.
- **Rectificaciones y ajustes:** Administrador documenta valores correctos, motivo
  y autorización. Las rectificaciones logísticas añaden compensaciones vinculadas;
  cantidad cero anula el efecto. Se conservan originales, versiones y auditorías.
- **Libro, grafo e historial:** contrastar base, eventos, saldos, documentos y fotos;
  descargar CSV cuando corresponda. El grafo representa relaciones registradas y no
  acredita por sí solo un recorrido físico completo.

Los controles bloquean stock insuficiente, versiones desactualizadas y periodos
cerrados. Los avisos permitidos requieren justificación; las reglas funcionan aunque
el modelo operativo no esté activo. Los cierres conservan balances por versión y
exigen sus condiciones; una reapertura y una rectificación posterior mantienen el
antecedente. Los documentos de negocio se identifican por referencia textual; la
carga de adjuntos operativos está disponible en la ficha del artículo.

En **Inventario actual → artículo → Actas y documentos de respaldo**, Administrador
u Operador adjunta PDF o fotografías PNG/JPEG/WebP de hasta 10 MB, indicando la
misma referencia documental que utilizó en la operación. Los tres roles pueden
consultar y descargar. Se conservan usuario, fecha, tamaño y huella SHA-256, con
auditoría del alta. La descarga exige autenticación y comprueba la huella del archivo.
Los documentos se relacionan por artículo y referencia; no constituyen aprobación
de un conteo ni un vínculo automático a una operación concreta. No hay eliminación
desde la interfaz. El respaldo de `storage/` incluye los adjuntos nuevos.

Preparación del inventario genera una ficha con espacios de conteo y firmas sin
aprobar existencias. En Áreas y catálogos, una baja se rechaza si conserva stock,
custodias o cuentas activas adscritas; el histórico mantiene su identidad.

## Validación independiente

1. Acordar el protocolo: objetivo, población, muestra, semilla, criterios, evidencias
   y responsables. Administrador/Auditor prepara un estudio de 1 a 5.000 filas,
   sin superar la población. La pantalla consulta el marco técnico y recalcula la
   recomendación documental; la institución confirma su elegibilidad.
2. Congelar selección, datos y huellas. El estudio documental usa transcripción
   vigente con fotos; el del detector usa exclusivamente su evaluación reservada.
3. Otra cuenta autorizada realiza el cotejo. El preparador y, para el detector, el
   entrenador de la versión no pueden etiquetar. La pantalla omite puntuaciones y
   decisiones previas; la independencia fuera del flujo debe comprobarse.
4. En estudios nuevos, registrar NORMAL, ANOMALO o INDETERMINADO para el detector.
   ANOMALO requiere identificar cantidad, fecha, tipo de operación o área con
   inconsistencia documental verificada, además del motivo y respaldo. Un
   indeterminado inicial requiere segundo cotejo registrado: si persiste, se informa
   separado del denominador principal. Las fotos alteradas invalidan la evidencia.
   Descargar el informe, que muestra seleccionados, evaluables y excluidos.

La concordancia por fila mide la transcripción vigente, no la exactitud del OCR
original. En estudios versión 2, positivo significa anomalía documental verificada,
no fraude. Los estudios anteriores conservan sus clases y cálculos; no se convierten
retrospectivamente. Precisión, recall y F1 se calculan cuando la muestra está revisada,
con indeterminados persistentes y denominadores informados; una división indefinida
permanece sin valor. Las etiquetas no se copian a HIL ni reentrenan el modelo.

Para nuevas versiones existe la opción de separación por artículo y documentos
relacionados. Conserva juntos artículos, lotes y fotografías, y evalúa artículos no
vistos; requiere suficientes grupos y suele depender de referencias globales. El
modelo del 20/10 no se sustituye automáticamente. Consultar el
[protocolo y los instrumentos de evaluación](PROTOCOLO_EVALUACION.md).

## Inicio, comprobaciones y respaldo

Con PostgreSQL y dependencias preparados, iniciar desde la raíz:

```powershell
.\iniciar-sistema.ps1
```

Interfaz: `http://localhost:5173/`. La API usa `VITE_API_BASE_URL`; por defecto,
`http://127.0.0.1:8000/api/v1`. En esta instalación está configurada en el puerto
8011. El iniciador lee los archivos de entorno de desarrollo en la misma precedencia
que Vite y comprueba el puerto configurado.
El iniciador usa la instalación existente; no inicializa la base. La conexión, claves
y demás configuración se guardan en `.env`, fuera de Git. Referencia de entorno:
Python 3.11 (entorno local) o 3.12 (instalación limpia comprobada), y Node 24,
o Node 22 desde 22.12. Este inicio corresponde a desarrollo local.

Desde `backend`, con su entorno Python, se pueden ejecutar:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m scripts.auditar_sistema --salida backups/auditoria_actual.json
.\.venv\Scripts\python.exe -m scripts.respaldo_recuperacion
```

Desde `frontend`: `npm ci`, `npm test -- --maxWorkers=2`,
`npm run lint -- --quiet` y `npm run build`. Las pruebas PostgreSQL se realizan en una
base QA nueva y marcada mediante `scripts.piloto_postgresql`. La restauración crea
otra base/carpeta y se verifica antes de reemplazar cualquier instalación. Los
planes de corrección ya aplicados o archivados no se reejecutan para producir informes.

## Instalación y producción

Las dependencias Python directas y transitivas están fijadas con hashes:
`backend/requirements/runtime.lock` para ejecución y
`backend/requirements/development.lock` para pruebas/desarrollo. Conservan las
versiones de scikit-learn, NumPy, SciPy y joblib del modelo existente. Instalar en
un entorno nuevo con Python 3.11 o 3.12:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements/development.lock
.\.venv\Scripts\python.exe -m pip check
```

En Linux, el ejecutable equivalente es `.venv/bin/python`. Para renovar las
dependencias, modificar los archivos fuente y regenerar ambos locks con
`uv pip compile --universal --python-version 3.11 --generate-hashes`, usando como
entradas `requirements/runtime.in` y `requirements.txt`, respectivamente. Repetir
pruebas y auditoría antes de distribuirlos. Las restricciones de `security.txt`
también protegen las instalaciones parciales. Los paquetes OCR experimentales
ajenos al circuito actual no forman parte del entorno mínimo.

La pila `compose.production.yml` tiene PostgreSQL 18 en un volumen propio,
migración previa al arranque de la API, ejecución sin recarga y sin usuario root,
frontend compilado servido por Nginx, y volúmenes privados para fotografías,
modelos, respaldos y registros. La API usa el rol `activos_app`, con lectura y
escritura de datos; el rol propietario se reserva para migraciones y recuperación.
El script de roles solo actúa sobre un volumen nuevo. La pila de desarrollo
existente conserva su configuración y sus volúmenes.

Copiar `produccion.env.example` a `.env.production` y sustituir las tres claves por
valores aleatorios distintos. `PUBLIC_ORIGIN` debe ser el origen HTTPS real.
`POSTGRES_*` construye la conexión sin concatenar contraseñas; también se mantiene
el soporte de `DATABASE_URL`, incluidos caracteres escapados en Alembic.

```powershell
docker compose --env-file .env.production -f compose.production.yml config --quiet
docker compose --env-file .env.production -f compose.production.yml up --build -d
docker compose --env-file .env.production -f compose.production.yml exec backend python -m scripts.seed_admin --email correo-institucional --nombre "Administrador responsable"
```

El último comando solicita la contraseña de forma privada y rechaza sustituir un
administrador existente. En el ejemplo se debe escribir un correo válido real.
Solo Nginx publica `127.0.0.1:8080`; API y base quedan en la red interna. Un proxy
HTTPS de la instalación debe dirigir el dominio a ese puerto. Verificar además
los proxies de confianza y la identificación de IP del cliente en la red elegida.
La cookie privada de fotografías es segura en producción y requiere HTTPS.
`/storage/` siempre pasa por la autenticación de la API; no se sirve como carpeta
pública. El frontend usa `/api/v1` en el mismo origen.

La configuración se comprobó con Compose, pero el motor Docker de este equipo
no consiguió iniciar durante la revisión del 30/10. Por ello, la construcción,
el arranque completo, HTTPS y la carga concurrente de esta pila siguen pendientes
de ensayo en un equipo con Docker operativo. Las imágenes base usan etiquetas:
registrar sus digests en la entrega institucional. No ejecutar `down -v` sobre
una instalación con datos que deban conservarse.

El respaldo local continúa usando `scripts.respaldo_recuperacion`. En contenedores,
ejecutarlo con la cuenta propietaria desde el servicio de migración:

```powershell
docker compose --env-file .env.production -f compose.production.yml run --rm migrate python -m scripts.respaldo_recuperacion
```

La recuperación crea una base QA independiente y verifica tablas, secuencias y
archivos; no reemplaza la base operativa. Las herramientas localizan `pg_dump` y
`pg_restore` mediante `POSTGRES_BIN`, PATH o la instalación de PostgreSQL en Windows.
El cliente de producción es de la misma versión mayor que su servidor. La copia
del volumen de respaldos a un destino externo y la restauración en el servidor
definitivo forman parte del procedimiento de entrega.

La compilación de dependencias sigue la [documentación oficial de uv](https://docs.astral.sh/uv/pip/compile/)
y el cliente Linux utiliza el [repositorio oficial PostgreSQL](https://www.postgresql.org/download/linux/debian/).

## Presentación y diseño

Demostrar: Kárdex y foto → HIL → fuente de cierre → inventario y libro → grafo →
reportes → calibración → pendientes de validación. Las operaciones de demostración
se realizan en QA con datos identificados como prueba.

Para calibración, proyectar el informe breve y consultar la guía del expositor
enlazados desde el [README](../README.md#material-de-calibración-local). Conservan los
mismos seis apartados y gráficos. El notebook y su paquete permiten reproducir el
experimento; para Colab se sube primero el cuaderno y luego el paquete cuando lo pida.
No hace falta reejecutarlo para abrir los HTML sin conexión. Los diagnósticos de
estabilidad y carga no sustituyen Ground Truth.

El diseño Mosaico uniforme mantiene colores y herramientas: tres columnas en
escritorio, dos intermedias y una en móvil. La ficha organiza sus bloques en columnas
y reserva el ancho completo a tablas y grafo. Las tarjetas admiten teclado y la
tabla de accesos contiene su desplazamiento horizontal en celular.

El logo original `frontend/src/assets/fundacion-patino.png` pertenece a la Fundación.
Su procedencia registrada es `https://fundacionpatino.org/lib/logo.png`, descargado
el 29/09/2026; se mantienen proporciones y colores. La paleta usa azul `#436986`,
fondo `#f5f7fa` y texto `#293e50`, definidos en `minimalist.css`.
