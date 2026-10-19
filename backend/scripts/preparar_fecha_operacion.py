"""Verifica la nueva fecha de operación en QA y respalda antes de migrar producción."""
import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from app.db.session import engine


ANTERIOR = "e35a7d2c9b14"
NUEVA = "f46b8e3d1a20"
QA = "activos_estado_qa_20261008t044004z"


def estado(conexion):
    return conexion.execute(text("""
        SELECT count(*), md5(coalesce(string_agg(
            (to_jsonb(m) - 'ocurrido_en')::text, '|' ORDER BY m.id), ''))
        FROM movimientos_kardex m
    """)).one()


def version(conexion):
    return conexion.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def migrar(objetivo, entorno):
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", objetivo],
                   env=entorno, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    url = engine.url
    qa = create_engine(url.set(database=QA), pool_pre_ping=True)
    with engine.connect() as conn:
        assert version(conn) == ANTERIOR, "La base principal no está en la revisión esperada"
        principal_antes = estado(conn)
    with qa.connect() as conn:
        assert version(conn) == ANTERIOR, "La copia QA no está en la revisión esperada"
        qa_antes = estado(conn)

    entorno_qa = os.environ.copy()
    entorno_qa["DATABASE_URL"] = url.set(database=QA).render_as_string(
        hide_password=False)
    migrar(NUEVA, entorno_qa)
    with qa.connect() as conn:
        assert version(conn) == NUEVA and estado(conn) == qa_antes
        assert conn.execute(text("""
            SELECT count(*) FROM movimientos_kardex WHERE ocurrido_en IS NOT NULL
        """)).scalar_one() == 0

    if args.aplicar:
        marca = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        respaldo = Path("backups") / f"fecha_operacion_{marca}.dump"
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
            assert version(conn) == ANTERIOR and estado(conn) == principal_antes, (
                "La base principal cambió durante el respaldo")
        migrar(NUEVA, entorno)
        with engine.connect() as conn:
            assert version(conn) == NUEVA and estado(conn) == principal_antes
        print(f"QA verificada; principal migrada; respaldo: {respaldo.resolve()}; "
              f"movimientos conservados: {principal_antes[0]}")
    else:
        print(f"QA verificada; principal sin cambios; movimientos QA: {qa_antes[0]}")


if __name__ == "__main__":
    main()
