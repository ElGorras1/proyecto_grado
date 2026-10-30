# Manual del sistema

Fundación Simón I. Patiño · Actualizado el 30/10/2026.
[Inicio](../README.md) · [Estado, pruebas y pendientes](ESTADO_Y_VALIDACION.md).

## Propósito y componentes

El sistema conserva Kárdex escaneados, permite revisar su transcripción y conecta el
histórico con el inventario operativo, sus documentos y la auditoría. Usa Vue 3 y
TypeScript, FastAPI, SQLAlchemy/Alembic y PostgreSQL. Gemini realiza la extracción
documental; Isolation Forest apoya la selección de movimientos para revisión.

## Herramientas y permisos

| Herramienta | Uso principal |
|---|---|
| Kárdex digital | Artículos, fotografías, cargas por tandas, historial, HIL y cobertura documental. |
| Inventario actual | Aperturas, existencias por área, ingresos, salidas, devoluciones, transferencias, custodias y rectificaciones. |
| Reportes | Consulta por gestión, artículo y área, movimientos y exportación. |
| Analítica y auditoría histórica | Reglas, versiones, entrenamiento, resultados y revisión de hallazgos. |
| Analítica de operaciones digitales | Controles y preparación de un modelo separado para eventos operativos. |
| Informe institucional y cierres anuales | Balances, cierre, reapertura y versiones conservadas. |
| Alertas y seguimiento | Evidencia, prioridad, asignación, revisión y conclusión de casos. |
| Preparación del inventario | Prioridades y fichas imprimibles para cotejar y contar. |
| Validación del proyecto | Estudios documentales y del detector, etiquetas independientes e informe verificable. |
| Gestión de usuarios | Cuentas, roles, estado y adscripción. |
| Áreas y catálogos | Ubicaciones operativas, catálogo histórico, alias y cambios auditados. |
| Registro de accesos | Consulta de accesos por fecha, usuario y resultado. |

Administrador tiene 12 accesos; Auditor, 11; Operador, 9. Los tres consultan
inventario, Kárdex y evidencia. Administrador gestiona cuentas y autoriza aperturas,
ajustes, rectificaciones y cierres. Operador registra operaciones y corrige lecturas
documentales con evidencia. Auditor revisa cobertura, estudios y casos; consulta
áreas y accesos, sin registrar movimientos de stock ni corregir OCR. Gestión de
usuarios es exclusiva de Administrador; Áreas y catálogos y Registro de accesos se
reservan a Administrador/Auditor. El servidor verifica los permisos en cada solicitud.

La adscripción de una cuenta identifica su área; el acceso operativo sigue regido
por rol. Una separación institucional adicional por área requiere definición y pruebas.

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

Las áreas inferidas se asignaron por parecido y frecuencias de artículo, hoja y
archivo; su soporte es heurístico, no una probabilidad validada. Se conserva la sigla
literal y la condición inferida. C+C es histórica e inactiva; CEDOC y CEDOAL conservan
identidades separadas. Confirmar un alias exige cotejo y motivo; no confirma las filas
previas. Desactivarlo impide nuevas asignaciones por esa lectura.

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
carga de adjuntos operativos sigue pendiente.

Preparación del inventario genera una ficha con espacios de conteo y firmas sin
aprobar existencias. En Áreas y catálogos, una baja se rechaza si conserva stock,
custodias o cuentas activas adscritas; el histórico mantiene su identidad.

## Validación independiente

1. Acordar el protocolo: objetivo, población, muestra, semilla, criterios, evidencias
   y responsables. Administrador/Auditor prepara un estudio de 1 a 100 filas.
2. Congelar selección, datos y huellas. El estudio documental usa transcripción
   vigente con fotos; el del detector usa exclusivamente su evaluación reservada.
3. Otra cuenta autorizada realiza el cotejo. El preparador y, para el detector, el
   entrenador de la versión no pueden etiquetar. La pantalla omite puntuaciones y
   decisiones previas; la independencia fuera del flujo debe comprobarse.
4. Registrar conclusión, motivo, referencia y declaración de independencia. Las
   dudas, errores documentales o fotos alteradas mantienen pendientes las métricas;
   no se retiran filas para mejorar el resultado. Descargar el informe verificable.

La concordancia por fila mide la transcripción vigente, no la exactitud del OCR
original. Para el detector, positivo significa «inusual relevante», no fraude.
Precisión, recall y F1 corresponden a la muestra completada; un denominador cero queda
sin definir. Las etiquetas no se copian automáticamente a HIL ni reentrenan el modelo.

## Inicio, comprobaciones y respaldo

Con PostgreSQL y dependencias preparados, iniciar desde la raíz:

```powershell
.\iniciar-sistema.ps1
```

Interfaz: `http://localhost:5173/`. API: `http://127.0.0.1:8000/`.
El iniciador usa la instalación existente; no inicializa la base. La conexión, claves
y demás configuración se guardan en `.env`, fuera de Git. Referencia de entorno:
Python 3.12 y Node 24, o Node 22 desde 22.12. La entrega de producción y su instalación
reproducible siguen pendientes; este inicio corresponde a desarrollo local.

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
