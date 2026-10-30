# Mosaico uniforme

Implementado el 30 de octubre de 2026 a partir de la propuesta visual seleccionada.

## Inicio

Las herramientas comparten tarjeta, icono, título, descripción y categoría. Se conservan
los colores institucionales y las rutas existentes. El mosaico presenta tres columnas
en escritorio, dos en pantallas intermedias y una en celular.

La visibilidad conserva los permisos: Administrador dispone de 12 accesos; Auditor, de
11; Operador, de 9. El cierre de sesión sigue disponible.

## Ficha del inventario

La ficha incorpora un índice con enlaces a las secciones disponibles y bloques de
ancho uniforme para existencias, base, operaciones, custodia, conciliación, controles
y correcciones. Las tablas del libro e historial y el grafo usan todo el ancho.
Los formularios permanecen visibles según las condiciones y permisos originales.

Los bloques se distribuyen en columnas para evitar huecos junto a formularios de
distinta altura. En celular se presentan en el orden del documento, en una columna.
Se conservan los avisos de fuente, conteo pendiente y bloqueos operativos.

Las tarjetas de los catálogos de inventario y Kárdex son botones nativos, accesibles
con teclado. La tabla de accesos contiene su desplazamiento horizontal en celular.

## Verificación

- 110 pruebas de interfaz aprobadas; comprobación estática y compilación aprobadas.
- 372 pruebas del servidor aprobadas y una omitida por sus condiciones de ejecución.
- Navegación revisada con datos reales, API de solo lectura y tres roles: inicio,
  inventario, ficha, Kárdex y accesos, en anchos de 1440, 768, 390 y 320 píxeles.
- Comparación del código de la ficha y del catálogo histórico: lógica intacta y
  154 enlaces originales de formularios y acciones conservados.

Esta revisión visual no modifica registros institucionales, fotografías, modelos
entrenados, etiquetas humanas ni sus requisitos pendientes. Los informes y datasets
generados en `outputs/` y los respaldos locales no se versionan.
