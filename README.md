# Sistema de Gestión y Trazabilidad de Activos Operativos

Fundación Simón I. Patiño · Documentación actualizada el 31/10/2026.

Digitaliza Kárdex, conserva fotografías y revisiones humanas, gestiona inventario y
operaciones por área, genera reportes y apoya la auditoría con reglas e Isolation Forest.

El uso cotidiano se organiza en cuatro espacios: **Artículos e inventario**,
**Revisiones y alertas**, **Reportes** y **Administración**. Reportes reúne movimientos,
resumen y cierre en apartados separados; consultar el archivo no exige registrar
un cierre. La bandeja abre la evidencia del aviso y conserva su origen.

La instalación comprueba datos nuevos cada cinco minutos y la necesidad de actualizar
el modelo cada treinta días. Usa los pesos conservados y guarda el seguimiento por
separado. Sin cambios omite el entrenamiento; con cambios suficientes puede preparar
un candidato, conservando la referencia en uso. Parámetros y estudios quedan en
herramientas avanzadas, sin exigir entrenamiento manual para el trabajo cotidiano.

## Documentación principal

| Leer | Documento | Contenido |
|---|---|---|
| Primero | Este README | Propósito, índice e inicio rápido. |
| Para usar y mantener | [Manual del sistema](docs/MANUAL_SISTEMA.md) | Módulos, roles, HIL, áreas, inventario, validación, respaldo y presentación. |
| Para revisar avances | [Estado, pruebas y pendientes](docs/ESTADO_Y_VALIDACION.md) | Datos del corte, modelo, pruebas, limitaciones y orden para terminar. |

El núcleo está implementado y comprobado técnicamente. La aceptación institucional,
los conteos reales, el dataset oficial, las métricas humanas y la entrega de producción
siguen pendientes; sus condiciones están reunidas en el documento de estado.

El archivo del proyecto llega hasta 2025. Los informes utilizan esa referencia al
abrir; Isolation Forest permite consultar por gestión y artículo y descargar toda
la auditoría filtrada con su versión y umbral. Un hallazgo enlaza directamente al
HIL y al grafo del artículo. Las 11 áreas conocidas están habilitadas; las
ubicaciones físicas, fuentes documentales y etiquetas humanas requieren cotejo.

Los ensayos digitales identificados por el titular se retiraron con respaldo y
auditoría. La instalación conserva el archivo histórico, sin operaciones digitales
ni aperturas activadas. Los saldos documentales no acreditan conteos físicos actuales.

## Inicio rápido

Con PostgreSQL y dependencias preparados, ejecutar desde la raíz:

```powershell
.\iniciar-sistema.ps1
```

Interfaz: `http://localhost:5173/`. La API utiliza el puerto indicado por
`VITE_API_BASE_URL` en los archivos de entorno del frontend: 8000 por defecto y
8011 en la instalación local revisada. El iniciador respeta esa configuración.
El inicio usa la instalación existente. El manual contiene las comprobaciones y el respaldo.

Para una instalación nueva, usar los archivos de dependencias fijadas y la sección
[Instalación y producción](docs/MANUAL_SISTEMA.md#instalación-y-producción).
`compose.production.yml` separa la aplicación compilada del modo de desarrollo;
su arranque en contenedores y la configuración HTTPS deben verificarse antes de la entrega.

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
