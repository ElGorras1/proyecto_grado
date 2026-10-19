"""Respalda, prueba en copia y aplica la migración de responsables si se solicita."""
import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from app.db.session import engine


ANTERIOR = "c48d5e9b6f02"


def huella(conn):
    return conn.execute(text("""
        SELECT count(*), md5(coalesce(string_agg(
            (to_jsonb(m) - 'encargado_id' - 'usuario_registrador_id'
             - 'encargado_nombre')::text, '|' ORDER BY m.id), ''))
        FROM movimientos_kardex m
    """)).one()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    marca = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    respaldo = Path("backups") / f"responsables_{marca}.dump"
    respaldo.parent.mkdir(exist_ok=True)
    url = engine.url
    with engine.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == ANTERIOR
    entorno = os.environ.copy()
    entorno["PGPASSWORD"] = url.password or ""
    pg = Path(os.environ.get("POSTGRES_BIN", r"C:\Program Files\PostgreSQL\18\bin"))
    conexion = ["-h", url.host or "localhost", "-p", str(url.port or 5432),
                "-U", url.username or "postgres"]
    subprocess.run([str(pg / "pg_dump.exe"), *conexion, "-Fc", "-f",
                    str(respaldo), url.database], env=entorno, check=True)
    copia_nombre = "activos_responsables_qa_" + marca.lower()
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{copia_nombre}"'))
    subprocess.run([str(pg / "pg_restore.exe"), *conexion, "--no-owner",
                    "--exit-on-error", "-d", copia_nombre, str(respaldo)],
                   env=entorno, check=True)
    copia = create_engine(url.set(database=copia_nombre))
    with copia.connect() as conn:
        antes = huella(conn)
    entorno_copia = entorno.copy()
    entorno_copia["DATABASE_URL"] = url.set(database=copia_nombre).render_as_string(hide_password=False)
    for objetivo in ("head", ANTERIOR, "head"):
        subprocess.run([sys.executable, "-m", "alembic", "upgrade" if objetivo == "head" else "downgrade",
                        objetivo], env=entorno_copia, check=True)
        with copia.connect() as conn:
            assert huella(conn) == antes, "La migración modificó movimientos previos"
    if args.aplicar:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    print(f"Respaldo: {respaldo.resolve()}; copia verificada: {copia_nombre}; aplicado: {args.aplicar}")


if __name__ == "__main__":
    main()
