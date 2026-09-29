"""Detectar reintentos de fotos idénticas y archivarlos sin perder OCR ni imágenes.

Ejecutar desde backend: python scripts/reparar_lotes_duplicados.py [--apply]
Sin --apply solo presenta el plan. --apply crea primero un ZIP recuperable.
"""
import argparse
import json
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.db.session import SessionLocal  # noqa: E402
from app.models.kardex import (  # noqa: E402
    LoteCarga, MovimientoKardex, MovimientoKardexArchivado, SolicitudCargaKardex,
)
from app.models.auditoria import AuditoriaSistema  # noqa: E402
from app.services.huella_lote import huella_de_paginas  # noqa: E402


def datos_movimiento(movimiento):
    return {
        columna.name: (valor.isoformat() if hasattr(valor, "isoformat") else valor)
        for columna in MovimientoKardex.__table__.columns
        if (valor := getattr(movimiento, columna.name)) is not None
    }


def paginas_de_lote(filas, total_esperado):
    por_pagina = defaultdict(set)
    for fila in filas:
        por_pagina[fila.numero_pagina].add(fila.ruta_imagen_respaldo)
    if set(por_pagina) != set(range(1, total_esperado + 1)):
        raise ValueError("Páginas incompletas o repetidas")
    rutas = []
    raiz_imagenes = (BACKEND / "storage" / "kardex_images").resolve()
    for numero in range(1, total_esperado + 1):
        if len(por_pagina[numero]) != 1:
            raise ValueError(f"Página {numero} con más de una imagen")
        ruta = (BACKEND / next(iter(por_pagina[numero]))).resolve()
        if not ruta.is_relative_to(raiz_imagenes) or not ruta.is_file():
            raise ValueError(f"Imagen no disponible o fuera de storage: {ruta}")
        rutas.append(ruta)
    return rutas


def main(apply):
    db = SessionLocal()
    try:
        lotes = {l.id: l for l in db.query(LoteCarga).all()}
        filas_por_lote = defaultdict(list)
        for fila in db.query(MovimientoKardex).filter(MovimientoKardex.lote_id.is_not(None)).order_by(MovimientoKardex.id):
            filas_por_lote[fila.lote_id].append(fila)

        grupos = defaultdict(list)
        rutas_por_lote = {}
        omitidos = []
        for lote_id, filas in filas_por_lote.items():
            articulos = {fila.articulo_id for fila in filas}
            if len(articulos) != 1:
                omitidos.append((lote_id, "artículos mezclados"))
                continue
            try:
                rutas = paginas_de_lote(filas, lotes[lote_id].total_imagenes)
            except (ValueError, KeyError) as exc:
                omitidos.append((lote_id, str(exc)))
                continue
            huella = huella_de_paginas([ruta.read_bytes() for ruta in rutas])
            articulo_id = next(iter(articulos))
            grupos[(articulo_id, huella)].append(lote_id)
            rutas_por_lote[lote_id] = rutas

        repetidos = {}
        for ids in grupos.values():
            ids.sort()
            original = ids[0]
            for duplicado in ids[1:]:
                if len(filas_por_lote[original]) != len(filas_por_lote[duplicado]):
                    raise RuntimeError(f"Lotes {original}/{duplicado}: misma foto, distinto número de filas; revisión humana necesaria")
                repetidos[duplicado] = original

        print("Lotes idénticos:", repetidos)
        print("Filas repetidas:", sum(len(filas_por_lote[i]) for i in repetidos))
        print("Lotes sin huella (faltan imágenes o estructura):", omitidos)
        if not apply:
            print("Vista previa; use --apply para respaldar y corregir.")
            return

        involucrados = sorted(set(repetidos) | set(repetidos.values()))
        respaldo = None
        if repetidos:
            carpeta = BACKEND / "backups"
            carpeta.mkdir(exist_ok=True)
            respaldo = carpeta / f"lotes_duplicados_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.zip"
            manifest = {
                "duplicado_de": repetidos,
                "lotes": {i: {"total_imagenes": lotes[i].total_imagenes,
                               "fecha_escaneo": lotes[i].fecha_escaneo.isoformat(),
                               "filas": [datos_movimiento(f) for f in filas_por_lote[i]]}
                          for i in involucrados},
            }
            with zipfile.ZipFile(respaldo, "w", compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
                for ruta in {r for i in involucrados for r in rutas_por_lote[i]}:
                    z.write(ruta, ruta.relative_to(BACKEND).as_posix())
            with zipfile.ZipFile(respaldo) as z:
                if z.testzip() is not None:
                    raise RuntimeError("El respaldo ZIP no pasó la comprobación de integridad")
            print("Respaldo verificado:", respaldo)

        # El archivo de BD y la retirada del inventario ocurren en una sola transacción.
        for duplicado, original in repetidos.items():
            for fila in filas_por_lote[duplicado]:
                db.add(MovimientoKardexArchivado(
                    movimiento_id=fila.id, lote_original_id=duplicado,
                    lote_canonico_id=original, datos=datos_movimiento(fila),
                ))
                db.delete(fila)
        db.flush()
        for (articulo_id, huella), ids in grupos.items():
            if db.query(SolicitudCargaKardex).filter_by(articulo_id=articulo_id, huella=huella).first():
                continue
            db.add(SolicitudCargaKardex(
                articulo_id=articulo_id, huella=huella,
                estado="COMPLETADO", lote_id=min(ids),
            ))
        if repetidos:
            db.add(AuditoriaSistema(
                usuario_id=None, accion="archivar_lotes_duplicados",
                recurso="lotes_carga", recurso_id=None,
                resultado="exito", fecha_hora=datetime.now(timezone.utc),
                detalle={"duplicado_de": repetidos, "respaldo": str(respaldo),
                         "filas_archivadas": sum(len(filas_por_lote[i]) for i in repetidos)},
            ))
        db.commit()
        print("Corrección confirmada; filas activas:", db.query(func.count(MovimientoKardex.id)).scalar())
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    main(parser.parse_args().apply)
