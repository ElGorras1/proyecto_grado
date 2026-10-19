"""Ensaya la migración de custodias externas en QA y respalda la base principal."""
import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from app.db.session import engine


ANTERIOR = "i94e6b0f3a52"
NUEVA = "j05f7c1a4b63"
QA = "activos_estado_qa_20261008t044004z"


def estado(conexion, *, migrada=False):
    apertura = "to_jsonb(a) - 'cantidad_custodia_externa'" if migrada else "to_jsonb(a)"
    return (
        conexion.execute(text("SELECT count(*) FROM movimientos_kardex")).scalar_one(),
        conexion.execute(text("""
            SELECT md5(coalesce(string_agg(to_jsonb(m)::text, '|'
                ORDER BY m.id), '')) FROM movimientos_kardex m
        """)).scalar_one(),
        conexion.execute(text(f"""
            SELECT md5(coalesce(string_agg(({apertura})::text, '|'
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


def comprobar_nuevo(conexion, original):
    assert version(conexion) == NUEVA and estado(conexion, migrada=True) == original
    assert conexion.execute(text("""
        SELECT count(*) FROM apertura_inventario
        WHERE cantidad_custodia_externa <> 0
    """)).scalar_one() == 0
    assert conexion.execute(text("SELECT count(*) FROM custodia_externa")).scalar_one() == 0
    assert conexion.execute(text("SELECT count(*) FROM evento_custodia_externa")).scalar_one() == 0


def migrar(entorno, destino):
    accion = "upgrade" if destino == NUEVA else "downgrade"
    subprocess.run([sys.executable, "-m", "alembic", accion, destino],
                   env=entorno, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    url = engine.url
    qa = create_engine(url.set(database=QA), pool_pre_ping=True)
    with engine.connect() as conn:
        assert version(conn) == ANTERIOR
        principal_antes = estado(conn)
    entorno_qa = os.environ.copy()
    entorno_qa["DATABASE_URL"] = url.set(database=QA).render_as_string(hide_password=False)
    with qa.connect() as conn:
        qa_version = version(conn)
        if qa_version == NUEVA:
            assert conn.execute(text("SELECT count(*) FROM custodia_externa")).scalar_one() == 0
            assert conn.execute(text("SELECT count(*) FROM evento_custodia_externa")).scalar_one() == 0
            qa_antes = estado(conn, migrada=True)
        else:
            assert qa_version == ANTERIOR
            qa_antes = estado(conn)
    if qa_version == NUEVA:
        migrar(entorno_qa, ANTERIOR)
        with qa.connect() as conn:
            assert version(conn) == ANTERIOR and estado(conn) == qa_antes

    migrar(entorno_qa, NUEVA)
    with qa.connect() as conn:
        comprobar_nuevo(conn, qa_antes)
    migrar(entorno_qa, ANTERIOR)
    with qa.connect() as conn:
        assert version(conn) == ANTERIOR and estado(conn) == qa_antes
    migrar(entorno_qa, NUEVA)
    with qa.connect() as conn:
        comprobar_nuevo(conn, qa_antes)

    if not args.aplicar:
        print("Migración, reversión y repetición verificadas en QA; principal sin cambios")
        return

    marca = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    respaldo = Path("backups") / f"custodias_{marca}.dump"
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
        comprobar_nuevo(conn, principal_antes)
    print(f"QA verificada; principal migrada; respaldo: {respaldo.resolve()}; "
          f"movimientos conservados: {principal_antes[0]}")


if __name__ == "__main__":
    main()
