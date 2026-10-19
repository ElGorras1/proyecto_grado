# Sistema de Gestión y Trazabilidad de Activos Operativos

**Fundación Simón I. Patiño · Estado documental: 18/10/2026, Bolivia.**

El sistema digitaliza Kárdex físicos y conserva su evidencia; permite corregir lecturas, consultar movimientos y gestiones, trabajar con inventario actual, transferencias y custodias, generar reportes y apoyar la auditoría mediante reglas e Isolation Forest.

La documentación vigente se reduce a **tres documentos, incluido este README**:

| Documento | Contenido |
|---|---|
| **README — este documento** | Funcionamiento, módulos, datos actuales, roles y operación técnica básica. |
| [Avances y pendientes](docs/AVANCES_Y_PENDIENTES.md) | Qué se completó, qué puede demostrarse y qué falta para terminar y evaluar el proyecto. |
| [Resumen único del HIL](docs/RESUMEN_HIL.md) | Criterios aplicados, correcciones, categorías, evidencia y límites de la revisión. |

## Estado actual de los datos

Última consulta documentada del 18/10, realizada en modo de solo lectura:

| Indicador | Resultado |
|---|---:|
| Movimientos conservados | 11.918 |
| Históricos, incluidos estados no activos | 11.908 |
| Históricos activos | 11.859 |
| Registros digitales sin lote histórico | 10 |
| Movimientos elegibles según los controles analíticos actuales | **8.367** |
| Artículos representados entre los elegibles | **356** |
| Gestiones de los elegibles | **2005–2025** |
| Cola de movimientos observados HIL tratada | 399 |
| Movimientos de esa cola sin avisos | 283 |
| Movimientos categorizados con marca conservada | 116 |
| Avisos sin categorizar | **0** |

Las tres tandas del escaneo previsto fueron incorporadas. La cobertura total del archivo físico requiere una comprobación institucional; no debe mantenerse como actual la antigua estimación de 30–40 % pendiente. Las cantidades de catálogo, lotes, fotos y movimientos son indicadores diferentes.

**Categorizar no confirma los datos inciertos.** Los 116 movimientos marcados siguen excluidos de la selección analítica. Los 8.367 elegibles tampoco equivalen a una validación humana exhaustiva de todo el archivo: son el conjunto que supera los controles actuales, antes de separar entrenamiento, calibración y evaluación.

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
| Analítica histórica | Isolation Forest, cortes y versiones, puntuaciones, fuentes y evaluación. El módulo existe; falta entrenar y evaluar una versión nueva con el corte depurado actual. |
| Analítica digital | Modelo distinto para operaciones posteriores al corte, con horas y contexto verificables. Su preparación y activación requieren datos suficientes y revisión. |

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

## Conservación de la documentación anterior

Los informes por lote, HTML, índices y documentos sustituidos se retiraron de `docs/` después de verificar su respaldo. Se conservan **132 archivos anteriores**, incluido el README previo, en un único [archivo histórico comprimido](backend/backups/documentacion_consolidada_20261018/documentacion_anterior.zip), con [manifiesto SHA256](backend/backups/documentacion_consolidada_20261018/manifiesto_originales.json).

Los archivos técnicos de evidencia permanecen accesibles en el respaldo, y las fotos, planes HIL y auditorías mantienen sus ubicaciones operativas. El ZIP y esos respaldos son locales y están fuera de Git; deben acompañar una entrega institucional que los necesite. El Excel histórico del 12/10 citado anteriormente no se encontró en su ruta de entrega y no se presenta como dataset actual.

**Regla de mantenimiento:** actualizar estos tres documentos. Los resultados detallados de nuevas ejecuciones van a sus respaldos técnicos; no crear otro documento de avance por cada lote ni reintroducir índices históricos en `docs/`.
