"""Propone revisiones documentales sin modificar artículos, filas ni fotografías.

Uso: python -m scripts.auditar_catalogo_historico --salida RUTA.json
"""

import argparse
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from rapidfuzz import fuzz
from sqlalchemy import text

from app.db.session import engine


BACKEND = Path(__file__).resolve().parents[1]
NUMERO_ROMANO = re.compile(r"\b(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)\b")


def normalizar(nombre: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", " ", sin_tildes).strip()


def ediciones(nombre: str) -> tuple:
    return (*re.findall(r"\d+", nombre), *NUMERO_ROMANO.findall(nombre))


def generar() -> dict:
    with engine.connect() as conn:
        articulos = conn.execute(text("SELECT id, nombre FROM activo ORDER BY id")).all()
        filas = conn.execute(text("""
            SELECT m.id, m.articulo_id, m.lote_id, m.numero_pagina, m.orden_fila,
                   m.fecha_movimiento, m.ingresos, m.salidas, m.saldo_registrado,
                   m.ruta_imagen_respaldo, l.tanda
            FROM movimientos_kardex m JOIN lotes_carga l ON l.id=m.lote_id
            WHERE m.estado='ACTIVO'
            ORDER BY m.articulo_id,m.lote_id,m.numero_pagina,m.orden_fila,m.id
        """)).all()
        solicitudes = conn.execute(text("""
            SELECT lote_id, articulo_id FROM solicitudes_carga_kardex
            WHERE estado='COMPLETADO' AND lote_id IS NOT NULL
        """)).all()
    candidatos = []
    for i, a in enumerate(articulos):
        na = normalizar(a.nombre)
        for b in articulos[i + 1:]:
            nb = normalizar(b.nombre)
            if ediciones(na) != ediciones(nb):
                continue
            similitud = fuzz.ratio(na, nb)
            if similitud >= 88:
                candidatos.append({"articulos": [a.id, b.id], "nombres": [a.nombre, b.nombre],
                                   "similitud": round(similitud, 1),
                                   "tipo": "TITULO_SIMILAR_REVISAR_EDICION"})
    por_lote = defaultdict(list)
    por_articulo = defaultdict(list)
    por_imagen = defaultdict(set)
    for f in filas:
        por_lote[f.lote_id].append(f)
        por_articulo[f.articulo_id].append(f)
        if f.ruta_imagen_respaldo:
            por_imagen[f.ruta_imagen_respaldo.replace("\\", "/")].add(f.articulo_id)
    lotes_multiples = [{"lote_id": lid, "articulos": sorted({f.articulo_id for f in fs})}
                       for lid, fs in por_lote.items() if len({f.articulo_id for f in fs}) > 1]
    solicitudes_distintas = [{"lote_id": lid, "articulo_solicitud": aid,
                              "articulos_filas": sorted({f.articulo_id for f in por_lote[lid]})}
                             for lid, aid in solicitudes if por_lote[lid]
                             and {f.articulo_id for f in por_lote[lid]} != {aid}]
    imagen_compartida = [{"ruta": ruta, "articulos": sorted(ids)}
                        for ruta, ids in por_imagen.items() if len(ids) > 1]
    # Compara contenido de fotos distintas en los lotes activos; un mismo hash
    # de archivo en dos artículos sería un candidato fuerte de asociación errónea.
    por_sha = defaultdict(list)
    faltantes = []
    for ruta, ids in sorted(por_imagen.items()):
        path = BACKEND / ruta
        if not path.is_file():
            faltantes.append(ruta)
            continue
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        por_sha[digest].append((ruta, sorted(ids)))
    contenido_compartido = []
    for digest, referencias in por_sha.items():
        ids = {aid for _, articulos_imagen in referencias for aid in articulos_imagen}
        if len(ids) > 1:
            contenido_compartido.append({"sha256": digest, "articulos": sorted(ids),
                                         "rutas": [ruta for ruta, _ in referencias]})
    interrupciones = []
    cierres = []
    for articulo_id, fs in por_articulo.items():
        anterior = None
        for f in fs:
            if anterior is not None and f.lote_id != anterior.lote_id:
                esperado = anterior.saldo_registrado + (f.ingresos or 0) - (f.salidas or 0)
                if f.saldo_registrado != esperado:
                    interrupciones.append({"articulo_id": articulo_id,
                                           "lote_anterior": anterior.lote_id,
                                           "lote_siguiente": f.lote_id,
                                           "movimiento_anterior": anterior.id,
                                           "movimiento_siguiente": f.id,
                                           "saldo_esperado": esperado,
                                           "saldo_documento": f.saldo_registrado,
                                           "diferencia": f.saldo_registrado - esperado})
            anterior = f
        ultimo = fs[-1]
        cierres.append({"articulo_id": articulo_id, "movimiento_id": ultimo.id,
                        "lote_id": ultimo.lote_id, "pagina": ultimo.numero_pagina,
                        "fila": ultimo.orden_fila, "fecha_ocr": ultimo.fecha_movimiento.isoformat(),
                        "saldo_documental": ultimo.saldo_registrado})
    return {"generado_utc": datetime.now(UTC).isoformat(),
            "alcance": {"articulos_catalogo": len(articulos), "articulos_con_filas": len(por_articulo),
                        "filas_historicas": len(filas)},
            "titulos_similares": candidatos,
            "lotes_asignados_a_multiples_articulos": lotes_multiples,
            "solicitudes_con_articulo_distinto": solicitudes_distintas,
            "rutas_de_imagen_compartidas": imagen_compartida,
            "contenido_de_imagen_compartido": contenido_compartido,
            "evidencia_faltante": faltantes,
            "interrupciones_entre_lotes": interrupciones,
            "cierres_disponibles": cierres,
            "interpretacion": "Solo candidatos. Ni similitud de título ni continuidad de saldo autorizan unir artículos o reordenar páginas sin revisar las fotos."}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--salida", required=True, type=Path)
    args = parser.parse_args()
    informe = generar()
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"salida": str(args.salida.resolve()),
                      "titulos_similares": len(informe["titulos_similares"]),
                      "interrupciones_entre_lotes": len(informe["interrupciones_entre_lotes"]),
                      "imagenes_compartidas": len(informe["contenido_de_imagen_compartido"]),
                      "faltantes": len(informe["evidencia_faltante"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
