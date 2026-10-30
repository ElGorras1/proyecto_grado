# Sistema de Gestión y Trazabilidad de Activos Operativos

Fundación Simón I. Patiño · Documentación actualizada el 30/10/2026.

Digitaliza Kárdex, conserva fotografías y revisiones humanas, gestiona inventario y
operaciones por área, genera reportes y apoya la auditoría con reglas e Isolation Forest.

## Documentación principal

| Leer | Documento | Contenido |
|---|---|---|
| Primero | Este README | Propósito, índice e inicio rápido. |
| Para usar y mantener | [Manual del sistema](docs/MANUAL_SISTEMA.md) | Módulos, roles, HIL, áreas, inventario, validación, respaldo y presentación. |
| Para revisar avances | [Estado, pruebas y pendientes](docs/ESTADO_Y_VALIDACION.md) | Datos del corte, modelo, pruebas, limitaciones y orden para terminar. |

El núcleo está implementado y comprobado técnicamente. La aceptación institucional,
los conteos reales, el dataset oficial, las métricas humanas y la entrega de producción
siguen pendientes; sus condiciones están reunidas en el documento de estado.

## Inicio rápido

Con PostgreSQL y dependencias preparados, ejecutar desde la raíz:

```powershell
.\iniciar-sistema.ps1
```

Interfaz: `http://localhost:5173/`. API: `http://127.0.0.1:8000/`.
El inicio usa la instalación existente. El manual contiene las comprobaciones y el respaldo.

## Material de calibración local

Se conservan dos documentos complementarios, disponibles en esta instalación:

- [Informe para proyectar](outputs/calibracion-isolation-forest-20261028/Calibracion_Isolation_Forest.html): métricas y gráficos con texto breve.
- [Guía del expositor](outputs/calibracion-isolation-forest-20261028/Guia_expositor_Isolation_Forest.html): mismos gráficos y explicación detallada.

El notebook, su paquete de reproducción, el Excel y los datos exportados se mantienen
como artefactos técnicos en `outputs/`. No son nuevos documentos de avance. Los
materiales locales no se incluyen en GitHub.

## Conservación y mantenimiento

Mantener **tres documentos principales y dos materiales de exposición**. Actualizar
su contenido en lugar de crear otro informe por cada tarea.

Los 22 originales de esta consolidación tienen respaldo verificado en
`backend/backups/documentacion_consolidada_20261030/documentacion_anterior.zip`, con
manifiesto SHA-256. Fotos, datos, modelos, evidencias de revisión y respaldos anteriores
conservan sus ubicaciones privadas. La documentación sustituida puede recuperarse de ese archivo.
