"""Respalda y verifica la migración de controles en una copia antes de aplicarla."""

import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from app.db.session import engine


ANTERIOR = "e72d6c4a1b90"
NUEVA = "f83c9a1e2d47"


def huella(conn):
    return conn.execute(text("""
        SELECT count(*), md5(coalesce(string_agg(
            (to_jsonb(m) - 'registrado_en' - 'alertas_control'
             - 'justificacion_alertas')::text, '|' ORDER BY m.id), ''))
        FROM movimientos_kardex m
    """)).one()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        if version != ANTERIOR:
            raise RuntimeError(f"Se requiere la versión {ANTERIOR}; actual: {version}")
    marca = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    respaldo = Path("backups") / f"control_movimientos_{marca}.dump"
    respaldo.parent.mkdir(exist_ok=True)
    url = engine.url
    env = os.environ.copy()
    env["PGPASSWORD"] = url.password or ""
    pg = Path(os.environ.get("POSTGRES_BIN", r"C:\Program Files\PostgreSQL\18\bin"))
    conexion = ["-h", url.host or "localhost", "-p", str(url.port or 5432),
                "-U", url.username or "postgres"]
    subprocess.run([str(pg / "pg_dump.exe"), *conexion, "-Fc", "-f",
                    str(respaldo), url.database], env=env, check=True)
    copia_nombre = "activos_control_qa_" + marca.lower()
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{copia_nombre}"'))
    subprocess.run([str(pg / "pg_restore.exe"), *conexion, "--no-owner",
                    "--exit-on-error", "-d", copia_nombre, str(respaldo)],
                   env=env, check=True)
    copia = create_engine(url.set(database=copia_nombre))
    with copia.connect() as conn:
        antes = huella(conn)
    entorno_copia = env.copy()
    entorno_copia["DATABASE_URL"] = url.set(database=copia_nombre).render_as_string(
        hide_password=False)
    for objetivo in (NUEVA, ANTERIOR, NUEVA):
        operacion = "upgrade" if objetivo == NUEVA else "downgrade"
        subprocess.run([sys.executable, "-m", "alembic", operacion, objetivo],
                       env=entorno_copia, check=True)
        with copia.connect() as conn:
            assert huella(conn) == antes, "La migración alteró datos de movimientos"
    if args.aplicar:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", NUEVA], check=True)
        with engine.connect() as conn:
            assert huella(conn) == antes, "Cambio inesperado durante la aplicación"
    print(f"Respaldo: {respaldo.resolve()}; copia verificada: {copia_nombre}; "
          f"aplicado: {args.aplicar}")


if __name__ == "__main__":
    main()
