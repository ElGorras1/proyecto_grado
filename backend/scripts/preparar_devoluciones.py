"""Ensaya la migración de devoluciones en QA y respalda la base principal."""
import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from app.db.session import engine


ANTERIOR = "h83d5a9e7c21"
NUEVA = "i94e6b0f3a52"
QA = "activos_estado_qa_20261008t044004z"


def estado(conexion):
    return (
        conexion.execute(text("SELECT count(*) FROM movimientos_kardex")).scalar_one(),
        conexion.execute(text("""
            SELECT md5(coalesce(string_agg((to_jsonb(m) - 'movimiento_origen_id'
                - 'devuelto_por')::text, '|' ORDER BY m.id), ''))
            FROM movimientos_kardex m
        """)).scalar_one(),
        conexion.execute(text("""
            SELECT md5(coalesce(string_agg(to_jsonb(a)::text, '|'
                ORDER BY a.articulo_id), '')) FROM apertura_inventario a
        """)).scalar_one(),
        conexion.execute(text("""
            SELECT md5(coalesce(string_agg(to_jsonb(e)::text, '|'
                ORDER BY e.activo_id, e.area_id), '')) FROM existencia e
        """)).scalar_one(),
        conexion.execute(text("SELECT count(*) FROM transferencia_area")).scalar_one(),
    )


def version(conexion):
    return conexion.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def migrar(entorno, destino):
    subprocess.run([sys.executable, "-m", "alembic", "upgrade" if destino == NUEVA else "downgrade",
                    destino], env=entorno, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    url = engine.url
    qa = create_engine(url.set(database=QA), pool_pre_ping=True)
    with engine.connect() as conn:
        assert version(conn) == ANTERIOR
        principal_antes = estado(conn)
    with qa.connect() as conn:
        assert version(conn) == ANTERIOR
        qa_antes = estado(conn)

    entorno_qa = os.environ.copy()
    entorno_qa["DATABASE_URL"] = url.set(database=QA).render_as_string(hide_password=False)
    migrar(entorno_qa, NUEVA)
    with qa.connect() as conn:
        assert version(conn) == NUEVA and estado(conn) == qa_antes
        assert conn.execute(text("""
            SELECT count(*) FROM movimientos_kardex
            WHERE movimiento_origen_id IS NOT NULL OR devuelto_por IS NOT NULL
        """)).scalar_one() == 0
    migrar(entorno_qa, ANTERIOR)
    with qa.connect() as conn:
        assert version(conn) == ANTERIOR and estado(conn) == qa_antes
    migrar(entorno_qa, NUEVA)
    with qa.connect() as conn:
        assert version(conn) == NUEVA and estado(conn) == qa_antes

    if not args.aplicar:
        print("Migración, reversión y repetición verificadas en QA; principal sin cambios")
        return

    marca = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    respaldo = Path("backups") / f"devoluciones_{marca}.dump"
    respaldo.parent.mkdir(exist_ok=True)
    pg = Path(os.environ.get("POSTGRES_BIN", r"C:\Program Files\PostgreSQL\18\bin"))
    entorno = os.environ.copy()
    entorno["PGPASSWORD"] = url.password or ""
    conexion = ["-h", url.host or "localhost", "-p", str(url.port or 5432),
                "-U", url.username or "postgres"]
    subprocess.run([str(pg / "pg_dump.exe"), *conexion, "-Fc", "-f",
                    str(respaldo), url.database], env=entorno, check=True)
    subprocess.run([str(pg / "pg_restore.exe"), "-l", str(respaldo)],
                   stdout=subprocess.DEVNULL, env=entorno, check=True)
    with engine.connect() as conn:
        assert version(conn) == ANTERIOR and estado(conn) == principal_antes
    migrar(entorno, NUEVA)
    with engine.connect() as conn:
        assert version(conn) == NUEVA and estado(conn) == principal_antes
    print(f"QA verificada; principal migrada; respaldo: {respaldo.resolve()}; "
          f"movimientos conservados: {principal_antes[0]}")


if __name__ == "__main__":
    main()
