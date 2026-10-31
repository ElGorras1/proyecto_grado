"""Separación por componentes de artículo, lote y fotografía; no modifica el corte."""

from collections import defaultdict
from random import Random

PARTES = ("entrenamiento", "calibracion", "evaluacion")


def claves(fila):
    resultado = [("articulo", str(fila["articulo_id"]))]
    if fila.get("lote_id") is not None:
        resultado.append(("lote", str(fila["lote_id"])))
    if fila.get("ruta_imagen_respaldo"):
        resultado.append(("foto", fila["ruta_imagen_respaldo"].replace("\\", "/")))
    return resultado


def particionar_por_articulo(filas, semilla):
    padres = {}

    def raiz(nodo):
        padres.setdefault(nodo, nodo)
        while padres[nodo] != nodo:
            padres[nodo] = padres[padres[nodo]]
            nodo = padres[nodo]
        return nodo

    for fila in filas:
        ns = claves(fila)
        for nodo in ns[1:]:
            a, b = sorted((raiz(ns[0]), raiz(nodo)))
            padres[b] = a
        raiz(ns[0])
    grupos = sorted({raiz(claves(f)[0]) for f in filas})
    if len(grupos) < 5:
        raise ValueError(
            "Separación por artículo insuficiente: se requieren al menos cinco grupos independientes de artículo, lote y fotografía."
        )
    Random(semilla).shuffle(grupos)
    n = max(1, int(len(grupos) * 0.2))
    cal, test = set(grupos[:n]), set(grupos[n : 2 * n])
    return [
        (
            "calibracion"
            if raiz(claves(f)[0]) in cal
            else "evaluacion" if raiz(claves(f)[0]) in test else "entrenamiento"
        )
        for f in filas
    ]


def auditar_particiones(filas, partes):
    if (
        len(filas) != len(partes)
        or len({f["id"] for f in filas}) != len(filas)
        or set(partes) - set(PARTES)
    ):
        raise ValueError("Filas o asignación de particiones inválidas.")
    observadas = defaultdict(set)
    for f, parte in zip(filas, partes):
        for clave in claves(f):
            observadas[clave].add(parte)
    cruces = {
        tipo: sorted(k[1] for k, v in observadas.items() if k[0] == tipo and len(v) > 1)
        for tipo in ("articulo", "lote", "foto")
    }
    return dict(
        sin_cruces=not any(cruces.values()),
        cruces=cruces,
        movimientos={p: partes.count(p) for p in PARTES},
        articulos={
            p: len({f["articulo_id"] for f, q in zip(filas, partes) if q == p}) for p in PARTES
        },
    )


def reconstruir_asignacion(filas, semilla):
    """Reconstrucción por recorrido del grafo, sin reutilizar la unión del particionador."""
    adyacentes = defaultdict(set)
    for f in filas:
        ns = claves(f)
        for a in ns:
            adyacentes[a].update(ns)
    componentes = {}
    for nodo in sorted(adyacentes):
        if nodo in componentes:
            continue
        pendientes = [nodo]
        grupo = set()
        while pendientes:
            x = pendientes.pop()
            if x in grupo:
                continue
            grupo.add(x)
            pendientes.extend(adyacentes[x] - grupo)
        for x in grupo:
            componentes[x] = min(grupo)
    grupos = sorted(set(componentes.values()))
    Random(semilla).shuffle(grupos)
    n = max(1, int(len(grupos) * 0.2))
    cal, test = set(grupos[:n]), set(grupos[n : 2 * n])
    return {
        f["id"]: (
            "calibracion"
            if componentes[claves(f)[0]] in cal
            else "evaluacion" if componentes[claves(f)[0]] in test else "entrenamiento"
        )
        for f in filas
    }
