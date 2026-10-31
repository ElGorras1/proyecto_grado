"""Respaldo coherente, restauración aislada y despliegue de la revisión n49.

python -m scripts.respaldo_recuperacion [--aplicar-migracion]
python -m scripts.respaldo_recuperacion --restaurar backups/respaldo_FECHA
Nunca restaura ni revierte la base institucional. Cada recuperación crea otra base.
"""

import argparse
import importlib
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from uuid import UUID

from sqlalchemy import create_engine, inspect, text

from app.db.session import engine
from app.core.postgres_tools import postgres_tool
from scripts.preparar_analitica import digest_tablas
from scripts.verificar_respaldo_actual import crear_zip, sha256_archivo, verificar_zip

BACKEND = Path(__file__).resolve().parents[1]
ANTERIOR = "m38c0d4f9e62"
NUEVA = "n49e15fa0d73"


def escribir(path, datos):
    path.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def secuencias(conn):
    salida = {}
    for nombre in inspect(conn).get_sequence_names():
        quoted = conn.dialect.identifier_preparer.quote(nombre)
        fila = conn.execute(text(f"SELECT last_value, is_called FROM {quoted}")).one()
        salida[nombre] = list(fila)
    return salida


def estado(conn):
    return {
        "tablas": digest_tablas(conn, inspect(conn).get_table_names()),
        "secuencias": secuencias(conn),
    }


def modelos_y_enlaces(conn, archivos):
    presentes = {f["ruta"]: f["sha256"] for f in archivos}
    faltantes = []
    for (ruta,) in conn.execute(
        text(
            "SELECT DISTINCT ruta_imagen_respaldo FROM movimientos_kardex "
            "WHERE ruta_imagen_respaldo IS NOT NULL"
        )
    ):
        normal = ruta.replace("\\", "/")
        if normal not in presentes:
            faltantes.append(normal)
    modelos = 0
    tablas = inspect(conn).get_table_names()
    for tabla, carpeta in (
        ("analitica_modelos", ".analytics"),
        ("analitica_operativa_modelos", ".analytics_operativa"),
    ):
        if tabla not in tablas:
            continue
        for id, digest in conn.execute(
            text(f"SELECT id, artefacto_sha256 FROM {tabla} WHERE estado='COMPLETADO'")
        ):
            if str(UUID(id)) != id:
                raise RuntimeError("Identidad de modelo inválida")
            if presentes.get(f"{carpeta}/{id}.joblib") != digest:
                raise RuntimeError("Modelo completo sin archivo privado íntegro en el respaldo")
            modelos += 1
    return {"modelos_privados_verificados": modelos, "imagenes_referenciadas_ausentes": faltantes}


def verificar_paquete(carpeta):
    manifiesto = json.loads((carpeta / "manifiesto.json").read_text(encoding="utf-8"))
    for archivo in ("base.dump", "archivos.zip"):
        esperado = manifiesto["paquete"][archivo]
        p = carpeta / archivo
        if p.stat().st_size != esperado["bytes"] or sha256_archivo(p) != esperado["sha256"]:
            raise RuntimeError(f"Respaldo alterado: {archivo}")
    for f in manifiesto["archivos"]:
        ruta = PurePosixPath(f["ruta"])
        if (
            ruta.is_absolute()
            or ".." in ruta.parts
            or "\\" in f["ruta"]
            or ":" in f["ruta"]
            or not ruta.parts
            or ruta.parts[0] not in ("storage", ".analytics", ".analytics_operativa")
        ):
            raise RuntimeError("El ZIP contiene una ruta no permitida")
    verificar_zip(carpeta / "archivos.zip", manifiesto["archivos"])
    return manifiesto


def nueva_copia(carpeta, marca, prefijo="activos_recuperacion_qa_"):
    manifiesto = verificar_paquete(carpeta)
    url = engine.url
    nombre = prefijo + marca.lower()
    if not re.fullmatch(r"activos_(recuperacion|continuacion)_qa_[a-z0-9_]+", nombre):
        raise RuntimeError("Nombre de recuperación no permitido")
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{nombre}"'))
    finally:
        admin.dispose()
    entorno, conexion, _ = parametros()
    subprocess.run(
        [
            str(postgres_tool("pg_restore")),
            *conexion,
            "--no-owner",
            "--exit-on-error",
            "-d",
            nombre,
            str(carpeta / "base.dump"),
        ],
        env=entorno,
        check=True,
    )
    copia = create_engine(url.set(database=nombre))
    with copia.connect() as conn:
        if estado(conn) != manifiesto["base"]:
            raise RuntimeError("La restauración no reconcilia tablas y secuencias")
    return copia, nombre, manifiesto


def parametros():
    url = engine.url
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("Esta herramienta requiere PostgreSQL")
    entorno = os.environ.copy()
    if url.password:
        entorno["PGPASSWORD"] = url.password
    pg = postgres_tool("pg_dump").parent
    conexion = [
        "-h",
        url.host or "localhost",
        "-p",
        str(url.port or 5432),
        "-U",
        url.username or "postgres",
    ]
    return entorno, conexion, pg


def respaldar(marca):
    carpeta = BACKEND / "backups" / ("respaldo_" + marca)
    carpeta.mkdir(parents=True, exist_ok=False)
    entorno, conexion, _ = parametros()
    # pg_dump usa el MISMO snapshot PostgreSQL que los conteos y hashes.
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        if conn.execute(
            text("SELECT 1 FROM solicitudes_carga_kardex WHERE estado='PROCESANDO' LIMIT 1")
        ).first():
            raise RuntimeError("Espera a que termine el escaneo en curso antes del respaldo")
        if conn.execute(text("SELECT 1 FROM analitica_modelos WHERE plaza=1 LIMIT 1")).first():
            raise RuntimeError("Espera al entrenamiento histórico antes del respaldo")
        if (
            "analitica_operativa_modelos" in inspect(conn).get_table_names()
            and conn.execute(
                text("SELECT 1 FROM analitica_operativa_modelos WHERE plaza=1 LIMIT 1")
            ).first()
        ):
            raise RuntimeError("Espera al entrenamiento operativo antes del respaldo")
        base = estado(conn)
        snapshot = conn.execute(text("SELECT pg_export_snapshot()")).scalar_one()
        subprocess.run(
            [
                str(postgres_tool("pg_dump")),
                *conexion,
                "-Fc",
                "--snapshot",
                snapshot,
                "-f",
                str(carpeta / "base.dump"),
                engine.url.database,
            ],
            env=entorno,
            check=True,
        )
        entradas = []
        for nombre in ("storage", ".analytics", ".analytics_operativa"):
            for p in sorted((BACKEND / nombre).rglob("*")):
                if p.is_file():
                    if p.is_symlink() or not p.resolve().is_relative_to(
                        (BACKEND / nombre).resolve()
                    ):
                        raise RuntimeError("Archivo fuera de la raíz de respaldo")
                    entradas.append((p, p.relative_to(BACKEND).as_posix()))
        archivos = crear_zip(carpeta / "archivos.zip", entradas)
        enlaces = modelos_y_enlaces(conn, archivos)
    paquete = {
        p.name: {"bytes": p.stat().st_size, "sha256": sha256_archivo(p)}
        for p in (carpeta / "base.dump", carpeta / "archivos.zip")
    }
    manifiesto = dict(
        creado_en=datetime.now(UTC).isoformat(),
        base=base,
        archivos=archivos,
        paquete=paquete,
        enlaces=enlaces,
        secretos_excluidos=True,
    )
    escribir(carpeta / "manifiesto.json", manifiesto)
    verificar_paquete(carpeta)
    return carpeta


def ensayar_y_aplicar(carpeta, marca, aplicar):
    copia, nombre, manifiesto = nueva_copia(carpeta, marca, "activos_continuacion_qa_")
    with copia.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    if version != ANTERIOR:
        raise RuntimeError("El ensayo de migración requiere la revisión " + ANTERIOR)
    env, _, _ = parametros()
    env["DATABASE_URL"] = copia.url.render_as_string(hide_password=False)
    tablas = {k: v for k, v in manifiesto["base"]["tablas"].items() if k != "alembic_version"}
    for accion, destino in (("upgrade", NUEVA), ("downgrade", ANTERIOR), ("upgrade", NUEVA)):
        subprocess.run([sys.executable, "-m", "alembic", accion, destino], env=env, check=True)
        with copia.connect() as conn:
            if digest_tablas(conn, list(tablas)) != tablas:
                raise RuntimeError("El ensayo alteró datos preexistentes")
    reporte = dict(
        copia=nombre,
        migracion=NUEVA,
        ensayo="upgrade-downgrade-upgrade correcto",
        tablas_preexistentes=len(tablas),
        aplicado=False,
    )
    if aplicar:
        from alembic.migration import MigrationContext
        from alembic.operations import Operations

        revision = importlib.import_module(
            "migrations.versions.n49e15fa0d73_analitica_operativa_cierres"
        )
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL lock_timeout='5s'"))
            conn.execute(text("SET LOCAL statement_timeout='60s'"))
            nombres = ", ".join(
                conn.dialect.identifier_preparer.quote(t)
                for t in sorted(manifiesto["base"]["tablas"])
            )
            conn.execute(text("LOCK TABLE " + nombres + " IN SHARE MODE"))
            if estado(conn) != manifiesto["base"]:
                raise RuntimeError("La base cambió desde el respaldo; repite la preparación")
            with Operations.context(MigrationContext.configure(conn)):
                revision.upgrade()
            conn.execute(
                text("UPDATE alembic_version SET version_num=:n WHERE version_num=:a"),
                {"n": NUEVA, "a": ANTERIOR},
            )
            if digest_tablas(conn, list(tablas)) != tablas:
                raise RuntimeError("La migración alteró datos preexistentes; transacción revertida")
            if secuencias(conn) | manifiesto["base"]["secuencias"] != secuencias(conn):
                raise RuntimeError("Secuencias preexistentes alteradas")
        reporte["aplicado"] = True
    escribir(carpeta / "migracion.json", reporte)
    copia.dispose()
    return reporte


def restaurar(carpeta, marca):
    copia, nombre, manifiesto = nueva_copia(carpeta, marca)
    destino = BACKEND / "backups" / ("recuperacion_" + marca)
    destino.mkdir(parents=True, exist_ok=False)
    raiz = (destino / "archivos").resolve()
    raiz.mkdir()
    with zipfile.ZipFile(carpeta / "archivos.zip") as z:
        for f in manifiesto["archivos"]:
            p = (raiz / f["ruta"]).resolve()
            if not p.is_relative_to(raiz):
                raise RuntimeError("Ruta de recuperación fuera del destino")
            p.parent.mkdir(parents=True, exist_ok=True)
            with z.open(f["ruta"]) as origen, p.open("xb") as salida:
                import shutil

                shutil.copyfileobj(origen, salida)
            if sha256_archivo(p) != f["sha256"]:
                raise RuntimeError("Archivo recuperado diferente")
    with copia.connect() as conn:
        enlaces = modelos_y_enlaces(conn, manifiesto["archivos"])
    reporte = dict(
        base_restaurada=nombre,
        archivos_recuperados=len(manifiesto["archivos"]),
        reconciliacion="Tablas, secuencias y SHA-256 de archivos coinciden",
        **enlaces,
    )
    escribir(destino / "verificacion.json", reporte)
    copia.dispose()
    return dict(carpeta=str(destino), **reporte)


def main():
    parser = argparse.ArgumentParser()
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--aplicar-migracion", action="store_true")
    grupo.add_argument("--restaurar", type=Path)
    args = parser.parse_args()
    marca = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    if args.restaurar:
        reporte = restaurar(args.restaurar.resolve(strict=True), marca)
    else:
        carpeta = respaldar(marca)
        if args.aplicar_migracion:
            reporte = dict(carpeta=str(carpeta), **ensayar_y_aplicar(carpeta, marca, True))
        else:
            copia, nombre, _ = nueva_copia(carpeta, marca)
            copia.dispose()
            reporte = dict(carpeta=str(carpeta), base_restaurada=nombre, resultado="VERIFICADO")
            escribir(carpeta / "verificacion.json", reporte)
    print(json.dumps(reporte, ensure_ascii=False))


if __name__ == "__main__":
    main()
