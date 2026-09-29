# Sistema de Gestión y Trazabilidad de Activos Operativos

**Caso institucional:** Fundación Simón I. Patiño<br>
**Estado del documento:** diagnóstico y hoja de ruta; actualización operativa del 29 de septiembre de 2026<br>
**Estado del producto:** prototipo funcional en transición hacia una arquitectura de inventario normalizada y auditable

## 1. Resumen ejecutivo

**Inicio simplificado:** la pantalla inicial ofrece tres accesos a Kárdex, Inventario y Reportes, junto con herramientas según el rol. Se retiraron de esa pantalla el resumen estadístico, el filtro anual y el enlace al panel de prueba administrativa. Las consultas por gestión se realizan en Reportes. Kárdex e Inventario comparten un buscador con el icono separado del campo para evitar superposiciones al escribir.

**Diseño de interfaz (29/09/2026):** paleta azul desaturada, fondos claros y espaciado consistente; logo oficial de la Fundación en el acceso y la cabecera. El panel reúne Inventario, Kárdex y Reportes en tres accesos principales, separados de las herramientas administrativas. Se preservan los colores de las alertas y las funciones existentes. Identidad y procedencia del logo documentadas en `frontend/src/assets/BRANDING.md`. Compilación y 9 pruebas frontend correctas; acceso y panel revisados visualmente en escritorio y móvil (390 px), con datos ficticios para el panel.

Este proyecto transforma un **Kárdex físico histórico en papel** en un **Inventario Digital Vivo y Trazable**. El sistema combina digitalización con IA multimodal, validación humana, control de stock, trazabilidad, seguridad por roles y auditoría institucional.

El dominio contiene dos flujos que comparten artículos, pero que no deben mezclarse durante la validación ni durante el análisis forense:

1. **Flujo Legacy (pasado):** fotografías de hojas físicas, extracción con Gemini, validación matemática y cronológica, clasificación de nodos y corrección Human-In-The-Loop (HIL).
2. **Flujo Moderno (presente y futuro):** operaciones digitales realizadas por usuarios autenticados: ingresos, ventas, transferencias, ferias, consignaciones, donaciones, bajas y anulaciones.

Actualmente ambos flujos se almacenan en `movimientos_kardex`. Esto permitió construir rápidamente el prototipo, pero esa tabla se convirtió en una **Tabla Dios** y debe separarse antes de escalar la digitalización completa.

### Estado de los datos

- **Actualización 28/09/2026:** la base contiene 4.330 movimientos preservados (4.321 históricos y 9 modernos). El histórico digitalizado abarca 79 artículos, 210 páginas y 87 lotes activos. La migración de calidad HIL identifica 425 filas pendientes: 91 alertas de saldo, 161 de fecha, 191 de área y 12 de referencia. Los tipos se superponen y no deben sumarse como filas únicas. No es una medida de precisión OCR ni de fraude.
- **Actualización 23/09/2026:** hay 3.047 movimientos activos (3.038 Legacy y 9 modernos). Se detectaron por comparación byte a byte de las fotos tres lotes repetidos: 65 y 66 eran reintentos del 64 de «HUMBERTO IPORRE SALINAS \"UNA SELECCION\"» (109 filas cada uno), y el 68 era reintento del 67 de «AGUSTINA Y ELLOS» (161 filas). Sus 379 filas duplicadas se archivaron en `movimientos_kardex_archivados`; las fotos y las lecturas OCR permanecen conservadas. El ZIP de respaldo íntegro está en `backend/backups/`. Los 65 lotes no repetidos quedaron identificados por una huella única de artículo y páginas ordenadas.
- La línea base del **18/09/2026** registraba 1.267 movimientos: 1.258 Legacy y 9 modernos. Esa cifra es histórica y ya no representa el volumen actual.
- Se estima que quedan entre **30.000 y 40.000 filas físicas** por procesar.
- También existe información nativa de 2026 en Excel/PDF pendiente de evaluación e importación.
- Estas cifras son una referencia operativa y deben confirmarse con un perfilado reproducible de la base antes de ejecutar la migración.

Documentos de control generados para iniciar el refactor:

- [Línea base técnica del 18 de septiembre de 2026](docs/baseline-2026-09-18.md).
- [Resultado de clasificación de áreas y referencias](docs/node-classification-2026-09-18.md).
- [ADR-0001: separación de movimientos Legacy y transacciones modernas](docs/adr/0001-separacion-legacy-moderno.md).

## 2. Flujos funcionales

### 2.1 Kárdex histórico (Legacy)

```text
Fotografías de hojas
        ↓
Compresión y conservación de evidencia
        ↓
Extracción estructurada con Gemini
        ↓
Validación aritmética y cronológica
        ↓
Clasificación de áreas/operaciones
        ↓
Auto-validación o bandeja HIL
        ↓
Histórico validado y saldo de corte
```

El sistema actualmente puede:

- Recibir lotes de imágenes.
- La carga espera la respuesta del procesamiento secuencial sin el antiguo corte de dos minutos;
  muestra el tiempo transcurrido y distingue errores de conexión de errores del servidor.
  Si hay una desconexión, repetir exactamente las mismas fotos y el mismo artículo ya no crea
  otro lote: devuelve el guardado, la confirmación pendiente, o indica que sigue procesando.
  El procesamiento como trabajo asíncrono recuperable sigue pendiente.
- Previsualizar, numerar y reordenar las fotografías antes de enviarlas al LLM.
- Exigir confirmación explícita de que las páginas pertenecen al artículo y están ordenadas de
  la más antigua a la más reciente.
- Convertir las imágenes a WebP y conservarlas como evidencia.
- Extraer filas estructuradas mediante Gemini.
- Detener un lote antes de guardarlo si la extracción no contiene páginas o una página no contiene
  movimientos. Si los encabezados difieren del artículo seleccionado, conserva la extracción y
  solicita confirmar o cancelar. La confirmación reutiliza la extracción sin llamar nuevamente a
  Gemini, registra al usuario y las diferencias en auditoría, y evita duplicar el lote al reintentar.
- Confirmar el lote y todos sus movimientos en una sola transacción, evitando lotes huérfanos.
- Validar la continuidad de ingresos, salidas y saldos.
- Detectar fechas fuera de secuencia.
- Clasificar movimientos hacia áreas, ventas, ferias, consignaciones, donaciones y otras operaciones.
- Resolver nombres de áreas mediante catálogo, sinónimos y fuzzy matching.
- Marcar errores matemáticos y nodos dudosos para revisión humana.
- Corregir registros desde la interfaz HIL.
- Mostrar un grafo dirigido interactivo de entradas y salidas, compatible con devoluciones y ciclos, con detalle por área y cantidades acumuladas.

### 2.2 Inventario moderno

```text
Usuario autenticado
        ↓
Operación de inventario
        ↓
Validación de cantidad y stock
        ↓
Registro del movimiento
        ↓
Actualización del saldo
        ↓
Auditoría institucional
```

El sistema actualmente permite:

- Crear artículos/productos.
- Registrar un saldo inicial.
- Registrar ingresos y salidas.
- Registrar datos específicos de transferencias, ferias, ventas, consignaciones, donaciones y bajas.
- Impedir salidas superiores al stock disponible.
- Consultar el historial moderno de cada artículo.
- Anular operaciones modernas.
- Recalcular los saldos posteriores después de una anulación.
- Registrar usuario, IP y detalles de las principales mutaciones.

> La anulación con recálculo en cascada es funcional para el volumen actual, pero no es la solución definitiva. Se reemplazará por transacciones compensatorias y una existencia actual persistida.

### 2.3 Reportes por gestión

El panel principal incluye **Reportes por gestión** (`/reportes/inventario`). Permite consultar
movimientos por año, mes, artículo/código, origen Legacy o moderno, dirección (ingreso/salida),
nodo y estado de revisión HIL. Muestra totales agregados, distribución mensual y detalle
paginado; el CSV exporta **todas** las filas que cumplen los filtros aplicados, no solo la página
visible. Los movimientos anulados se excluyen de las sumas y del CSV.

La gestión se toma de `fecha_movimiento`: inicialmente es la fecha extraída del papel, pero
puede corregirse con evidencia conservando `fecha_original`. Como esa fecha puede ser errónea y no determina el orden físico, el reporte
**no debe interpretarse como existencia al cierre de año**. «Sin alertas HIL» significa que no
hay alertas de saldo, fecha, área o referencia activas, no una certificación humana integral.

### 2.4 Calidad HIL y dashboard operativo

- El HIL separa saldo, fecha, área y referencia. El recálculo Legacy respeta lote/página/fila,
  no reescribe saldos ni notas originales y no modifica operaciones modernas.
- `tiene_error_fecha` conserva el hallazgo cronológico. `fecha_estado` distingue `SIN_ALERTA`,
  `PENDIENTE_HIL`, `CORREGIDA` y `CONFIRMADA_DOCUMENTO`. Confirmar una fecha tal como aparece
  en la foto resuelve la revisión, sin ocultar que está fuera de secuencia ni inventar otra fecha.
- La revisión presenta fotografía y formulario juntos, exige motivo, conserva datos originales
  y expone el historial de valores anteriores/nuevos y autoría. Corrección y auditoría se
  confirman en una sola transacción. El Auditor consulta; Administrador y Operador corrigen.
- Los datos previos a esta migración son una **línea base conservada**, no una reconstrucción de
  valores OCR que pudieran haberse sobrescrito antes. Las nuevas extracciones conservan el JSON
  por fila con la fuente `EXTRACCION_MLLM`.
- El dashboard principal muestra catálogo, suma referencial de últimos saldos, actividad moderna
  por gestión/mes, calidad global del histórico y artículos prioritarios con acceso directo a HIL.
  No calcula stock por área, cierres anuales, precisión OCR ni resultados de Isolation Forest.
- El escaneo conserva su flujo sencillo sin colas ni Redis: límites configurables (20 páginas,
  20 MB por imagen, 100 MB por lote, 60 MP), validación de contenido JPEG/PNG/WebP y detección de
  páginas idénticas dentro del lote **antes** de gastar cuota de IA. La idempotencia de reintentos
  entre lotes sigue activa. Aún requiere mantener la pantalla abierta mientras procesa.

Migración aplicada localmente: `e04f1b5d2a68`. Respaldo previo recuperable en
`backend/backups/pre_calidad_hil_20260929T035012Z.json.gz` (fecha UTC). La reconciliación confirmó
4.330 filas y cero cambios en fechas de consulta, cantidades, textos, nodos o rutas de evidencia;
solo se recalcularon indicadores derivados y se añadieron campos de conservación/calidad.

Para otro entorno: generar respaldo con `python -m scripts.respaldar_calidad_hil`, ejecutar
`alembic upgrade head` y verificar con `python -m scripts.verificar_calidad_hil RUTA_RESPALDO`.

QA visual reproducible (sin datos reales ni escrituras): con Vite en desarrollo, abrir
`/qa/calidad.html`. Esta vista usa los mismos componentes con respuestas ficticias y no forma
parte del build de producción.

Verificación de este hito: 54 pruebas backend, 9 pruebas frontend y build TypeScript/Vite
correctos, consultas de solo lectura sobre PostgreSQL y revisión visual de los componentes en
escritorio/móvil con datos de prueba. No se hicieron llamadas nuevas a Gemini ni revisiones
humanas ficticias sobre la base real.

## 3. Seguridad y perfiles

Los endpoints de Kárdex, reportes y dashboard requieren autenticación; las mutaciones principales aplican RBAC.

| Rol | Capacidades actuales |
|---|---|
| Administrador | Gestión de usuarios, operaciones de inventario, digitalización, correcciones y reportes de acceso |
| Operador | Digitalización, correcciones HIL y operaciones de inventario |
| Auditor | Consultas, trazabilidad, errores HIL y reporte de accesos |

La decisión de permitir que el `Operador` corrija registros HIL y que el `Auditor` solo consulte debe ser ratificada como regla institucional.

Controles implementados:

- JWT con expiración configurable.
- Hash de contraseñas con Argon2.
- Guardas de navegación en Vue.
- Validación de autenticación y roles en FastAPI.
- Rate limiting en el login.
- Baja lógica de usuarios.
- Protección contra la desactivación del último administrador.
- Auditoría de inicios de sesión y mutaciones administrativas/operativas principales.

Pendiente para afirmar que el sistema está completamente endurecido:

- Matriz automatizada rol × endpoint.
- Límites de carga a nivel de proxy/servidor HTTP adicionales a los controles ya implementados en la API.
- Revocación o rotación de sesiones/tokens.
- Pruebas de concurrencia sobre el stock.
- Auditoría y operación dentro de una única transacción SQL.

## 4. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Frontend | Vue 3, TypeScript estricto, Vite, Pinia, PrimeVue |
| Visualización | Apache ECharts y Cytoscape.js |
| Backend | Python 3.12, FastAPI, Pydantic |
| Persistencia | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Seguridad | Argon2, JWT, RBAC, SlowAPI |
| IA multimodal | Google Gemini mediante `google-genai` |
| Clasificación auxiliar | TheFuzz/RapidFuzz |
| Analítica planificada | pandas, NumPy, scikit-learn, Isolation Forest |
| Infraestructura local | Docker y Docker Compose |

## 5. Arquitectura actual

```text
Vue 3 / Pinia
      │  Axios + JWT
      ▼
FastAPI / RBAC / Auditoría
      ├── Autenticación
      ├── Usuarios
      ├── Reporte de accesos
      └── Kárdex
            ├── Gemini + imágenes
            ├── Validación/HIL
            ├── Inventario moderno
            └── Grafo dirigido de entradas y salidas
      │
      ▼
PostgreSQL
```

### Estructura principal

```text
proyecto-activos/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── api/              # dependencias y endpoints REST
│   │   ├── core/             # configuración, JWT, Argon2 y rate limiting
│   │   ├── crud/             # usuarios y auditoría
│   │   ├── db/               # engine y sesiones SQLAlchemy
│   │   ├── models/           # modelos ORM
│   │   ├── schemas/          # contratos Pydantic
│   │   └── services/         # Gemini, validación y clasificación
│   ├── init_db/              # esquema inicial PostgreSQL
│   ├── migrations/           # configuración de migraciones
│   ├── scripts/              # semillas administrativas
│   ├── storage/              # imágenes de respaldo del Kárdex
│   └── tests/                # pruebas PyTest
└── frontend/
    └── src/
        ├── components/       # componentes y grafos
        ├── router/           # rutas y guardas RBAC
        ├── services/         # cliente Axios
        ├── stores/           # estado de autenticación
        └── views/            # pantallas funcionales
```

### Pantallas disponibles

- Login.
- Panel principal.
- Administración.
- Gestión de usuarios.
- Reporte de accesos.
- Kárdex Digital Continuo.
- Inventario Actual en Vivo.
- Acceso denegado.

## 6. Modelo de datos actual

El scaffold contiene modelos para:

- Seguridad: `rol`, `permiso`, `rol_permiso`, `usuario`, `area`.
- Catálogo: `categoria_activo`, `activo`.
- Inventario diseñado originalmente: `existencia`, `tipo_movimiento`, `movimiento`.
- Migración documental: `documento_legacy`, `extraccion_legacy`, `validacion_legacy`.
- Analítica: `resultado_regla`, `evaluacion_anomalia`.
- Auditoría: `alerta`, `caso_auditoria`, `revision_caso`, `auditoria_sistema`.
- Implementación activa del prototipo: `lotes_carga`, `movimientos_kardex`.
- Catálogos auxiliares: áreas, sinónimos y ferias.

Aunque varias tablas institucionales están modeladas, el flujo operativo visible usa principalmente `movimientos_kardex`. `existencia`, el ledger original y el módulo de anomalías todavía no son la fuente de verdad de la aplicación.

## 7. Observaciones y deuda técnica conocida

### 7.1 Tabla Dios `movimientos_kardex`

La tabla mezcla campos Legacy (`lote_id`, página, imagen, errores OCR) con campos modernos (`feria_id`, receptor, canal y motivo de baja).

El problema principal no es el costo de almacenar valores `NULL`; 40.000 filas son manejables para PostgreSQL. Los riesgos reales son:

- Reglas de negocio incompatibles.
- Diferentes niveles de confianza y validación.
- Permisos distintos.
- Contaminación de la analítica forense.
- Dificultad para imponer constraints adecuados.
- Acoplamiento entre correcciones históricas y stock vivo.

### 7.2 HIL no escalable

La bandeja actual usa principalmente banderas rojas/amarillas. Al procesar el archivo completo puede crecer más rápido que la capacidad humana.

Se necesita clasificar cada fila como:

- `AUTO_VALIDADO`.
- `AUTO_CORREGIDO` con regla y evidencia.
- `REQUIERE_HUMANO`.
- `RECHAZADO`.

La extracción original de Gemini nunca debe sobrescribirse; toda corrección debe conservar valor anterior, valor nuevo, regla, usuario y fecha.

### 7.3 Recálculo en cascada

El stock actual se infiere desde el último `saldo_registrado`. Al anular una operación se actualizan todos los movimientos posteriores.

Esto introduce:

- Trabajo O(n).
- Bloqueos prolongados.
- Riesgo de carreras concurrentes.
- Mutación de historia ya auditada.
- Dificultad para cerrar periodos.

La solución será un ledger inmutable, transacciones compensatorias y una proyección `existencia_actual` actualizada en O(1).

### 7.4 Isolation Forest y calidad de datos

El histórico OCR no debe alimentar el modelo forense. Un error de lectura no equivale a fraude.

Isolation Forest se entrenará únicamente con transacciones modernas, validadas, no anuladas y con suficiente volumen. Su resultado significará **anomalía que requiere investigación**, no confirmación automática de robo o fraude.

### 7.5 Auditoría no completamente atómica

La operación de negocio y su registro de auditoría realizan commits separados. Si el segundo commit falla, la operación puede existir sin su evento de auditoría. El refactor debe usar una sola unidad transaccional.

### 7.6 Migraciones

El esquema inicial fue reparado recientemente y las dependencias de IA ya están declaradas. Sin embargo, la migración Alembic existente no representa todavía la evolución completa del esquema. Antes del refactor se debe establecer una línea base real y generar migraciones aditivas verificables.

### 7.7 Cobertura de pruebas

Existen pruebas para autenticación, RBAC, usuarios, auditoría y un componente de grafo. Falta cubrir de forma suficiente:

- Matriz completa de autorización.
- Carga y fallo parcial de lotes.
- Validación aritmética y cronológica.
- Clasificación de nodos.
- Correcciones HIL.
- Registro concurrente de movimientos.
- Anulación y compensación.
- Migración y reconciliación de datos.
- Componentes completos de Kárdex e Inventario Vivo.

### 7.8 Áreas o referencias no identificadas

La ausencia real de un dato no equivale a una lectura OCR dudosa. El sistema conserva el texto
original y clasifica por separado el estado del área y de la referencia.

- El valor OCR original permanece en `area`, `referencia` y la imagen de respaldo.
- Ventas, ferias, donaciones o consignaciones reconocibles conservan su nodo operativo aunque el
  campo área esté vacío.
- Un ingreso sin área usa `Origen no especificado`; una salida usa `Destino no especificado`. Ambos
  representan ausencia documental y no ubicaciones físicas reales.
- Un área legible sin equivalencia usa `AREA_NO_CATALOGADA` y pasa a HIL.
- Texto ilegible, símbolos o una coincidencia difusa usan `PENDIENTE_HIL`.
- Las coincidencias exactas o sinónimos confirmados usan `RESUELTA_AUTOMATICAMENTE`.
- Una corrección confirmada usa `RESUELTA_POR_HUMANO`.
- La referencia se clasifica independientemente como `PRESENTE`, `AUSENTE`, `ILEGIBLE` o
  `INCIERTA`; su ausencia no crea por sí sola un nodo.
- El grafo muestra entradas en verde y salidas en ámbar. Las áreas pendientes de revisión se
  distinguen por un borde discontinuo y una etiqueta en la tabla de detalle. Los nodos sin área
  registrada conservan su nombre explícito. La vista permite seleccionar un nodo, reintentar
  errores de carga y salir mientras hay una consulta pendiente; no depende de un Sankey sin ciclos.
- En el flujo moderno no se permiten nodos vacíos; deben seleccionarse explícitamente.

Solo `AREA_NO_CATALOGADA`, `PENDIENTE_HIL`, `ILEGIBLE` e `INCIERTA` requieren revisión humana. La
ausencia confirmada se conserva como una característica auditable. Ninguno de estos estados constituye
por sí solo fraude.

## 8. Arquitectura objetivo

```text
LEGACY                                  MODERNO
──────                                  ───────
lote_importacion                        saldo_apertura aprobado
      ↓                                          ↓
documento/pagina_fuente                 transaccion_inventario (inmutable)
      ↓                                          ↓
extraccion_ocr_fila                     existencia_actual
      ↓                                          ↓
movimiento_historico                    snapshot_existencia
      ↓                                          ↓
validacion_historica                    evaluacion_anomalia
      └──────── saldo de corte ─────────────────┘
```

### Tablas objetivo

| Capa | Tablas propuestas | Responsabilidad |
|---|---|---|
| Ingesta | `lote_importacion`, `documento_fuente`, `extraccion_ocr_fila` | Evidencia y resultado original inmutable |
| Legacy normalizado | `movimiento_historico`, `validacion_historica` | Normalización, reglas, HIL y trazabilidad de correcciones |
| Transición | `corte_inventario`, `saldo_apertura` | Punto aprobado entre pasado y operación viva |
| Operación | `transaccion_inventario` | Ledger moderno append-only |
| Proyección | `existencia_actual` | Stock actual por artículo y área |
| Histórico rápido | `snapshot_existencia` | Cierres periódicos para reportes |
| Analítica | `modelo_anomalia`, `evaluacion_anomalia` | Versiones de modelos y scores |
| Auditoría | `caso_auditoria`, `revision_caso` | Investigación y conclusión humana |

Antes de crear nuevas tablas se evaluará la reutilización de `documento_legacy`, `extraccion_legacy`, `validacion_legacy`, `existencia`, `movimiento` y las tablas de auditoría ya presentes.

## 9. Plan de avance

### Fase 0 — Congelar y medir el sistema actual

Objetivo: crear una línea base confiable antes de modificar datos.

- Generar backup completo de PostgreSQL e inventario de archivos de evidencia.
- Contar registros por tabla, artículo, lote y origen.
- Medir errores rojos/amarillos, duplicados y continuidad de saldos.
- Crear un conjunto de prueba anonimizado con casos reales.
- Documentar la matriz de permisos.
- Escribir un ADR que apruebe la separación Legacy/Moderno.
- Ejecutar y registrar PyTest, Vitest, lint y build.

**Criterio de salida:** backup recuperable, perfilado reproducible y comportamiento actual protegido por pruebas.

### Fase 1 — Blindaje SQA antes del refactor

- Tests unitarios para validación aritmética, cronología y clasificación.
- Tests de integración para carga, corrección, movimiento y anulación.
- Tests parametrizados rol × endpoint.
- Pruebas de concurrencia sobre el stock.
- Fixtures representativas de OCR correcto, ambiguo y erróneo.

**Criterio de salida:** cualquier cambio de comportamiento relevante rompe una prueba antes de llegar a producción.

### Fase 2 — Migración aditiva de base de datos

- Crear nuevas tablas sin eliminar `movimientos_kardex`.
- Incorporar constraints, claves foráneas e índices.
- Mantener la extracción original como evidencia inmutable.
- Separar por regla verificable:
  - `lote_id IS NOT NULL` → Legacy.
  - `lote_id IS NULL` → Moderno.
- Reconciliar conteos, sumas, saldos, fechas y muestras.
- Mantener scripts de migración idempotentes y reversibles cuando sea posible.

**Criterio de salida:** 100 % de los registros migrados o explicados, sin diferencias de saldo no justificadas.

### Fase 3 — Ledger moderno y existencia actual

- Implementar `transaccion_inventario` append-only.
- Usar FK al usuario, no nombres copiados.
- Actualizar `existencia_actual` con bloqueo transaccional.
- Reemplazar anulaciones destructivas por transacciones compensatorias.
- Añadir clave de idempotencia.
- Prohibir modificaciones de periodos cerrados.
- Registrar operación y auditoría en una sola transacción.

**Criterio de salida:** registrar o revertir una operación tiene costo O(1) y no reescribe el historial.

### Fase 4 — HIL escalable

- Incorporar códigos de error y severidad.
- Auto-validar casos consistentes.
- Auto-corregir únicamente cuando exista una solución determinística única.
- Detectar duplicados y continuidad entre páginas.
- Agrupar errores por causa raíz y permitir resolución masiva.
- Reutilizar sinónimos confirmados.
- Resolver áreas `AREA_NO_CATALOGADA` y `PENDIENTE_HIL` sin borrar el texto OCR original.
- Medir tasa de auto-validación y falsos positivos.

**Criterio de salida:** la cola humana crece solamente con casos ambiguos o institucionalmente sensibles.

### Fase 5 — Isolation Forest

- Seleccionar exclusivamente transacciones modernas validadas.
- Crear un pipeline reproducible de features y preprocesamiento.
- Versionar artefacto, parámetros, features, ventana y umbral.
- Implementar `POST /analitica/entrenar` como trabajo asíncrono con `job_id`.
- Guardar scores por transacción y versión de modelo.
- Operar inicialmente en modo sombra, sin bloquear movimientos.
- Evaluar deriva y reentrenar por ventana o cambio significativo.

Features iniciales candidatas:

- Cantidad absoluta y proporción respecto al stock previo.
- Tipo de operación.
- Frecuencia por usuario, artículo, receptor y área.
- Hora, día y estacionalidad.
- Destinos o receptores nuevos.
- Reversiones recientes.
- Desviación respecto a artículos o categorías comparables.

**Criterio de salida:** cada alerta es reproducible, explicable por contexto y deriva a revisión humana.

### Fase 6 — Dashboard ejecutivo

El dashboard operativo inicial ya está implementado con consultas agregadas sobre el modelo
actual. La fase final ampliará los indicadores sobre el inventario refactorizado:

- Stock y movimientos modernos.
- Progreso de digitalización.
- Calidad OCR y carga de HIL.
- Anomalías por prioridad.
- Casos de auditoría abiertos/cerrados.
- Trazabilidad por artículo, área y periodo.

La interfaz consume endpoints agregados; la migración futura reemplazará su fuente actual de
`movimientos_kardex` por el ledger y las existencias persistidas.

## 10. Qué se puede hacer inmediatamente

Mientras se diseña la migración, se puede avanzar de forma segura en:

1. Crear el backup y perfilado de los 1.267 registros actuales.
2. Convertir casos reales en fixtures de prueba.
3. Completar la matriz de pruebas RBAC.
4. Probar exhaustivamente el validador y clasificador actuales.
5. Diseñar el diccionario de datos de las tablas objetivo.
6. Preparar la migración Alembic aditiva.
7. Definir formalmente el saldo y fecha de corte entre Legacy y Moderno.
8. Diseñar las transacciones compensatorias.
9. Medir qué porcentaje del HIL puede resolverse mediante reglas determinísticas.
10. Definir las métricas ejecutivas del futuro dashboard.

Se pueden seguir procesando **lotes pequeños y controlados** para mejorar reglas y obtener fixtures. No se recomienda cargar las 30.000–40.000 filas restantes en la Tabla Dios antes de completar, como mínimo, las fases 0–3.

## 11. Instalación con Docker

Requisitos:

- Docker Desktop o Docker Engine con Compose.
- Una clave válida de Google AI Studio para procesar imágenes.

Desde la raíz del proyecto:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

En Windows PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Editar `backend/.env` y reemplazar como mínimo:

```env
JWT_SECRET_KEY=una-clave-larga-y-aleatoria
GEMINI_API_KEY=tu-clave-real
```

Levantar servicios:

```bash
docker compose up --build
```

Servicios:

- PostgreSQL: `localhost:5432`.
- FastAPI: `http://localhost:8000`.
- Swagger/OpenAPI: `http://localhost:8000/docs`.
- Vue/Vite: `http://localhost:5173`.

Crear el administrador inicial una sola vez:

```bash
docker compose exec backend python -m scripts.seed_admin
```

Las credenciales incluidas por la semilla son únicamente para desarrollo y deben cambiarse antes de cualquier despliegue institucional.

## 12. Instalación manual

### Inicio rápido en PowerShell (instalación local existente)

Desde la carpeta `proyecto-activos`, con PostgreSQL local iniciado:

```powershell
.\iniciar-sistema.ps1
```

El script comprueba el entorno de Python, Vite y PostgreSQL; inicia API e interfaz
en segundo plano y confirma sus direcciones. Abre `http://localhost:5173/`.
Los registros de arranque quedan en `%TEMP%\sistema-activos-logs`.
No ejecutes `seed_admin` ni recrees la base de datos para un inicio normal.

### Base de datos

```bash
createdb activos_db
psql -d activos_db -f backend/init_db/initial_schema.sql
```

### Backend

```bash
cd backend
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar y ejecutar:

```bash
pip install -r requirements.txt
python -m scripts.seed_admin
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## 13. Calidad y verificación

### Backend

```bash
cd backend
ruff check app tests
black --check app tests
pytest -v
```

### Frontend

```bash
cd frontend
npm run lint
npm test
npm run build
```

### Resultado de la última verificación local

Verificación realizada el 18 de septiembre de 2026 sobre la revisión `58d3caf`:

| Comprobación | Resultado |
|---|---|
| `npm run lint` | Correcto |
| `npm test` | Correcto: 1 archivo y 1 prueba |
| `npm run build` | Correcto: TypeScript y build de producción |
| PyTest del backend | Correcto: 26 pruebas, incluidas 6 de caracterización Kárdex |
| Ruff/Black de archivos nuevos | Correcto |
| Ruff global | 153 observaciones preexistentes pendientes de normalización |
| Docker Compose | No verificado en esta sesión: el daemon de Docker no estaba activo |

PyTest se ejecutó con Python 3.12 en un entorno temporal porque el `.venv` versionado localmente referencia una instalación de Python que ya no existe. La suite debe repetirse dentro de Docker o en un entorno virtual nuevo antes del siguiente hito.

### Verificación manual mínima

1. Iniciar sesión con cada rol.
2. Confirmar que una petición sin token obtiene `401`.
3. Confirmar que un rol autenticado sin permiso obtiene `403`.
4. Crear un producto y registrar saldo inicial.
5. Registrar ingreso y salida.
6. Intentar una salida superior al stock.
7. Cargar un lote Legacy pequeño.
8. Corregir una fila HIL y revisar la evidencia.
9. Verificar el evento correspondiente en `auditoria_sistema`.
10. Verificar que el stock y el historial sean consistentes.

## 14. Migraciones y política de esquema

El archivo `initial_schema.sql` permite iniciar una base nueva, pero todo cambio futuro debe realizarse mediante Alembic.

```bash
cd backend
alembic current
alembic history
alembic revision --autogenerate -m "descripcion_del_cambio"
alembic upgrade head
```

Reglas para el refactor:

- No eliminar ni renombrar `movimientos_kardex` en la primera migración.
- No modificar datos sin backup.
- Cada backfill debe producir un reporte de reconciliación.
- Las migraciones se prueban primero sobre una copia restaurable.
- No mezclar cambios de esquema con entrenamiento del modelo ML.

## 15. Principios del proyecto

- La evidencia original es inmutable.
- Una corrección nunca borra el valor anterior.
- Legacy y Moderno no se mezclan en el entrenamiento forense.
- Una anomalía no es automáticamente fraude.
- El stock moderno se actualiza transaccionalmente.
- Las anulaciones se representan mediante compensaciones.
- Toda operación sensible debe ser atribuible a usuario, fecha e IP.
- Los modelos y umbrales analíticos deben estar versionados.
- Ningún dashboard debe convertirse en una fuente alternativa de verdad.

## 16. Próximo hito recomendado

El siguiente hito debe reunir las fases 0 y 1:

> **Baseline SQA y diseño aprobado de migración Legacy/Moderno.**

Entregables:

- Backup restaurable.
- Perfilado de datos actual.
- Matriz RBAC automatizada.
- Suite de caracterización del Kárdex.
- Diccionario de datos objetivo.
- ADR de separación arquitectónica.
- Primera migración Alembic aditiva revisada, todavía sin eliminar la tabla actual.

Este hito reduce el riesgo del refactor y permite que el trabajo posterior de HIL, Isolation Forest y dashboard se construya sobre datos confiables.
