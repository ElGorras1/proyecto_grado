"""Verifica la migración de alertas en QA y respalda antes de aplicarla a la principal."""
import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from app.db.session import engine

ANTERIOR = "k16a8d2b7c40"
NUEVA = "l27b9c3e8d51"
QA = "activos_estado_qa_20261008t044004z"
TABLAS = ("movimientos_kardex", "apertura_inventario", "existencia",
          "custodia_externa", "evento_custodia_externa", "transferencia_area")


def estado(conn):
    resultado = {}
    for tabla in TABLAS:
        datos = "to_jsonb(t) - 'alertas_control' - 'justificacion_alertas'" if tabla == "transferencia_area" else "to_jsonb(t)"
        resultado[tabla] = tuple(conn.execute(text(
            f"SELECT count(*), md5(coalesce(string_agg(({datos})::text, '|' ORDER BY ({datos})::text), '')) FROM {tabla} t"
        )).one())
    return resultado


def version(conn):
    return conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def migrar(env, destino):
    subprocess.run([sys.executable, "-m", "alembic", "upgrade" if destino == NUEVA else "downgrade", destino], env=env, check=True)


def comprobar(conn, esperado):
    assert version(conn) == NUEVA and estado(conn) == esperado, "Cambió el inventario durante la migración"
    assert conn.execute(text("SELECT count(*) FROM transferencia_area WHERE alertas_control IS NOT NULL OR justificacion_alertas IS NOT NULL")).scalar_one() == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    url = engine.url
    qa = create_engine(url.set(database=QA), pool_pre_ping=True)
    assert url.database != QA, "La principal y QA deben ser distintas"
    with engine.connect() as conn:
        assert version(conn) == ANTERIOR
        principal = estado(conn)
    env_qa = os.environ.copy()
    env_qa["DATABASE_URL"] = url.set(database=QA).render_as_string(hide_password=False)
    with qa.connect() as conn:
        qa_version = version(conn)
        assert qa_version in (ANTERIOR, NUEVA)
        anterior = estado(conn)
        if qa_version == NUEVA:
            comprobar(conn, anterior)
    if qa_version == NUEVA:
        migrar(env_qa, ANTERIOR)
    migrar(env_qa, NUEVA)
    with qa.connect() as conn:
        comprobar(conn, anterior)
    migrar(env_qa, ANTERIOR)
    with qa.connect() as conn:
        assert version(conn) == ANTERIOR and estado(conn) == anterior
    migrar(env_qa, NUEVA)
    with qa.connect() as conn:
        comprobar(conn, anterior)
    if not args.aplicar:
        print("Migración y reversión verificadas en QA; principal sin cambios")
        return
    respaldo = Path("backups") / f"revision_controles_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.dump"
    respaldo.parent.mkdir(exist_ok=True)
    pg = Path(os.environ.get("POSTGRES_BIN", r"C:\Program Files\PostgreSQL\18\bin"))
    env_pg = os.environ.copy(); env_pg["PGPASSWORD"] = url.password or ""
    conexion = ["-h", url.host or "localhost", "-p", str(url.port or 5432), "-U", url.username or "postgres"]
    subprocess.run([str(pg / "pg_dump.exe"), *conexion, "-Fc", "-f", str(respaldo), url.database], env=env_pg, check=True)
    subprocess.run([str(pg / "pg_restore.exe"), "-l", str(respaldo)], env=env_pg, stdout=subprocess.DEVNULL, check=True)
    with engine.connect() as conn:
        assert version(conn) == ANTERIOR and estado(conn) == principal
    migrar(os.environ.copy(), NUEVA)
    with engine.connect() as conn:
        comprobar(conn, principal)
    print(f"Principal migrada; {principal['movimientos_kardex'][0]} movimientos conservados; respaldo: {respaldo.resolve()}")


if __name__ == "__main__":
    main()
