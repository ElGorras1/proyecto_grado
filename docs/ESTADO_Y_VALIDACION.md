# Estado, pruebas y pendientes

Consolidación: 30/10/2026, Bolivia. Datos institucionales comprobados el 29/10;
interfaz y pruebas generales comprobadas el 30/10. Esta edición de documentación no
realiza una auditoría nueva de datos. [Inicio](../README.md) · [Manual](MANUAL_SISTEMA.md).

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
| C07: entrega reproducible | Pendiente: dependencias, instalación, configuración, recuperación final y pruebas de despliegue/carga. |
| Interfaz | Mosaico uniforme aplicado el 30/10, con herramientas y permisos conservados. |

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
| Suite general del servidor | 372 aprobadas y 1 omitida por requerir PostgreSQL; 30/10. |
| Interfaz | 110 aprobadas; análisis estático y compilación correctos; 30/10. |
| Piloto PostgreSQL aislado | 160 aprobadas, sin omisiones; 29/10. No sumar a la suite general: cubre pruebas solapadas. |
| Revisión del rediseño con datos reales | 28 comprobaciones: tres roles, inicio/inventario/ficha/Kárdex/accesos y anchos 1440, 768, 390 y 320; 30/10. Cero errores JS/API, desbordamientos de página o escrituras. |
| Conservación de lógica de interfaz | 154 enlaces originales de formularios/acciones conservados entre ficha y catálogo histórico; 30/10. |
| Base y recuperación | Respaldos restaurados y reconciliados; migración aplicada `u16a75c1d380`; comprobación documental del 29/10. |

El 29/10 la auditoría del entorno Python reportó 19 avisos en cinco paquetes, con
18 identificadores distintos: certifi, dnspython, filelock, pypdf y setuptools.
Npm no reportó vulnerabilidades conocidas. Falta revisar alcance y actualizar o
retirar dependencias con pruebas de compatibilidad; aquel análisis no demostró la
explotabilidad de cada aviso. El resultado sin avisos del 18/10 es un antecedente.

Medianas locales del 29/10, con tres lecturas ASGI/PostgreSQL y sin concurrencia:
catálogo 2,769 s; perfil analítico 4,255 s; informe institucional 5,737 s. No son una
prueba de carga ni tiempos de extremo a extremo. Los catálogos siguen mostrando
todos sus artículos; la paginación y simplificación de analítica pueden mejorar el uso.

## Orden para terminar

1. **Entrega técnica C07:** revisar dependencias, fijar versión instalable, configurar
   producción y permisos, restaurar el respaldo final y medir carga/concurrencia.
2. **Fuentes y áreas:** cotejar cierres/cobertura; resolver o justificar bloqueos,
   inferencias y siglas; aprobar áreas, participantes y alcance de permisos.
3. **Inventario real C05:** aclarar el artículo de prueba, contar y ubicar existencias,
   adjuntar referencias/actas y aceptar el circuito con personal autorizado.
4. **Evaluación C06:** aprobar protocolo, realizar cotejo y etiquetas independientes,
   medir resultados y mejorar el diseño temporal. La calidad del OCR original y
   la evaluación académica del grafo requieren mediciones específicas si el alcance las exige.
5. **Dataset y expediente:** cerrar versión, diccionario, exclusiones, procedencia y
   huellas; obtener aprobación institucional y preparar conclusiones de la defensa.
6. **Modelo operativo:** entrenar y evaluar cuando existan suficientes eventos reales
   y representativos, si forma parte del alcance acordado.

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

Actualizar los tres documentos principales y los dos materiales de calibración
cuando corresponda. Guardar resultados detallados en sus expedientes técnicos y
evitar nuevos informes narrativos de avance que dupliquen este resumen.
