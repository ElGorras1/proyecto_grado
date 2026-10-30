"""Selección reproducible de filas históricas para revisión documental humana."""

import hashlib
import json


CAMPOS_DOCUMENTALES = (
    "fecha_movimiento", "detalle", "referencia", "area", "ingresos", "salidas",
    "saldo_registrado", "nodo_grafo", "fecha_estado", "area_estado",
    "referencia_estado", "ruta_imagen_respaldo",
)


def huella_fila(movimiento) -> str:
    """Permite advertir si la fila cambió desde la decisión humana."""
    datos = {campo: getattr(movimiento, campo) for campo in CAMPOS_DOCUMENTALES}
    for campo in ("fecha_documental_texto", "fecha_precision"):
        if getattr(movimiento, campo, None) is not None:
            datos[campo] = getattr(movimiento, campo)
    contenido = json.dumps(datos, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(contenido.encode()).hexdigest()


def seleccionar_ids(estratos: dict[str, list[int]], limite: int, semilla: str) -> list[int]:
    """Intercala estratos y ordena cada uno con una huella estable de sus IDs."""
    ordenados = {
        nombre: sorted(ids, key=lambda movimiento_id: (
            hashlib.sha256(f"{semilla}:{nombre}:{movimiento_id}".encode()).digest(),
            movimiento_id,
        ))
        for nombre, ids in estratos.items()
    }
    seleccionados: list[int] = []
    while len(seleccionados) < limite and any(ordenados.values()):
        for nombre in sorted(ordenados):
            if ordenados[nombre] and len(seleccionados) < limite:
                seleccionados.append(ordenados[nombre].pop(0))
    return seleccionados
