"""Respalda y verifica el estado actual sin modificar la base operativa.

Uso: python -m scripts.verificar_respaldo_actual --fuentes-tanda2 RUTA
El directorio backups/ contiene el dump, los archivos y la comprobación de
restauración. La base de prueba se conserva para una inspección posterior.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from app.db.session import engine


BACKEND = Path(__file__).resolve().parents[1]
CHUNK = 1024 * 1024


def sha256_archivo(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def snapshot_db(db_engine) -> dict:
    """Cuenta y compara contenido de todas las tablas públicas, sin exportar datos al informe."""
    with db_engine.connect() as conn:
        tablas = sorted(inspect(conn).get_table_names(schema="public"))
        resultado = {}
        for nombre in tablas:
            quoted = conn.dialect.identifier_preparer.quote(nombre)
            rows = conn.execute(text(f"SELECT row_to_json(t)::text FROM {quoted} t"))
            hashes = sorted(hashlib.sha256(row.encode("utf-8")).digest() for (row,) in rows)
            digest = hashlib.sha256()
            for item in hashes:
                digest.update(item)
            resultado[nombre] = {"filas": len(hashes), "sha256": digest.hexdigest()}
        return resultado


def crear_zip(destino: Path, archivos: list[tuple[Path, str]]) -> list[dict]:
    manifiesto = []
    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_STORED,
                         allowZip64=True) as archive:
        for path, arcname in archivos:
            archive.write(path, arcname)
            manifiesto.append({"ruta": arcname, "bytes": path.stat().st_size,
                               "sha256": sha256_archivo(path)})
    return manifiesto


def verificar_zip(destino: Path, manifiesto: list[dict]) -> None:
    """Descomprime cada entrada y contrasta sus bytes y SHA-256 con la fuente."""
    with zipfile.ZipFile(destino) as archive:
        assert set(archive.namelist()) == {r["ruta"] for r in manifiesto}
        for entry in manifiesto:
            digest = hashlib.sha256()
            size = 0
            with archive.open(entry["ruta"]) as stream:
                for block in iter(lambda: stream.read(CHUNK), b""):
                    digest.update(block)
                    size += len(block)
            if size != entry["bytes"] or digest.hexdigest() != entry["sha256"]:
                raise RuntimeError(f"Copia de archivo distinta: {entry['ruta']}")


def archivos_fuente(root: Path) -> list[tuple[Path, str]]:
    metadata = [root / "LEEME.txt", root / "manifest.csv", root / "plan_carga.csv",
                root / "_revision" / "estado_importacion.json"]
    originales = sorted((root / "originales").glob("*.jpg"))
    if len(originales) != 166 or any(not p.is_file() for p in metadata):
        raise RuntimeError("Faltan los originales o los metadatos de la tanda 2")
    with (root / "manifest.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 166 or {r["archivo_original"] for r in rows} != {p.name for p in originales}:
        raise RuntimeError("El manifiesto no corresponde a los 166 originales")
    for row in rows:
        p = root / "originales" / row["archivo_original"]
        if p.stat().st_size != int(row["bytes"]) or sha256_archivo(p) != row["sha256"]:
            raise RuntimeError(f"Original distinto del manifiesto: {p.name}")
    return [(p, "tanda_2/" + p.relative_to(root).as_posix())
            for p in [*metadata, *originales]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fuentes-tanda2", type=Path, required=True)
    args = parser.parse_args()
    marca = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    carpeta = BACKEND / "backups" / f"estado_actual_{marca}"
    carpeta.mkdir(parents=True, exist_ok=False)
    reporte = {"creado_utc": datetime.now(UTC).isoformat(),
               "carpeta": str(carpeta), "resultado": "INCOMPLETO"}
    reporte_path = carpeta / "verificacion.json"

    try:
        fuente = args.fuentes_tanda2.resolve(strict=True)
        antes = snapshot_db(engine)
        url = engine.url
        pg_bin = Path(os.environ.get("POSTGRES_BIN", r"C:\Program Files\PostgreSQL\18\bin"))
        conexion = ["-h", url.host or "localhost", "-p", str(url.port or 5432),
                    "-U", url.username or "postgres"]
        entorno = os.environ.copy()
        if url.password:
            entorno["PGPASSWORD"] = url.password

        dump = carpeta / "base.dump"
        subprocess.run([str(pg_bin / "pg_dump.exe"), *conexion, "-Fc", "-f",
                        str(dump), url.database], env=entorno, check=True)
        subprocess.run([str(pg_bin / "pg_restore.exe"), "-l", str(dump)],
                       stdout=subprocess.DEVNULL, env=entorno, check=True)
        despues = snapshot_db(engine)
        if antes != despues:
            raise RuntimeError("La base cambió durante el respaldo; repetir en una ventana estable")
        reporte["base"] = {"archivo": dump.name, "bytes": dump.stat().st_size,
                           "sha256": sha256_archivo(dump), "tablas": antes}

        app_files = [p for area in (BACKEND / "storage", BACKEND / ".analytics")
                     for p in sorted(area.rglob("*")) if p.is_file()]
        app_entries = [(p, p.relative_to(BACKEND).as_posix()) for p in app_files]
        app_manifest = crear_zip(carpeta / "evidencia_aplicacion.zip", app_entries)
        verificar_zip(carpeta / "evidencia_aplicacion.zip", app_manifest)
        source_manifest = crear_zip(carpeta / "fuentes_tanda2.zip", archivos_fuente(fuente))
        verificar_zip(carpeta / "fuentes_tanda2.zip", source_manifest)
        (carpeta / "manifiesto_archivos.json").write_text(
            json.dumps({"aplicacion": app_manifest, "fuentes_tanda2": source_manifest},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        reporte["archivos"] = {
            "aplicacion": len(app_manifest), "fuentes_tanda2": len(source_manifest),
            "zip_aplicacion_sha256": sha256_archivo(carpeta / "evidencia_aplicacion.zip"),
            "zip_fuentes_sha256": sha256_archivo(carpeta / "fuentes_tanda2.zip"),
            "verificacion": "Todas las entradas descomprimidas y comparadas por bytes y SHA-256",
        }

        nombre_copia = "activos_estado_qa_" + marca.lower()
        admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
        with admin.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{nombre_copia}"'))
        admin.dispose()
        reporte["base_restaurada"] = nombre_copia
        subprocess.run([str(pg_bin / "pg_restore.exe"), *conexion, "--no-owner",
                        "--exit-on-error", "-d", nombre_copia, str(dump)],
                       env=entorno, check=True)
        restaurada = create_engine(url.set(database=nombre_copia))
        try:
            copia = snapshot_db(restaurada)
        finally:
            restaurada.dispose()
        if copia != antes:
            raise RuntimeError("La restauración no coincide con la base de origen")
        reporte["resultado"] = "VERIFICADO"
        reporte["verificacion_bd"] = "Todas las tablas: conteo y SHA-256 de cada fila coinciden"
    except Exception as exc:
        reporte["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        reporte_path.write_text(json.dumps(reporte, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        print(json.dumps({"carpeta": str(carpeta), "resultado": reporte["resultado"],
                          "base_restaurada": reporte.get("base_restaurada"),
                          "error": reporte.get("error")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
