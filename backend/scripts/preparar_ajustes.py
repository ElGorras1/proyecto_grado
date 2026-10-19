"""Prueba la migración de ajustes en QA y respalda antes de aplicarla."""
import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from app.db.session import engine


ANTERIOR = "j05f7c1a4b63"
NUEVA = "k16a8d2b7c40"
QA = "activos_estado_qa_20261008t044004z"
CAMPOS = ("corrige_movimiento_id", "cantidad_anterior", "cantidad_corregida",
          "motivo_correccion", "autorizado_por_id")


def version(conn):
    return conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def estado(conn, *, migrada=False):
    expresion = "to_jsonb(m)" + "".join(f" - '{campo}'" for campo in CAMPOS) if migrada else "to_jsonb(m)"
    return (
        conn.execute(text("SELECT count(*) FROM movimientos_kardex")).scalar_one(),
        conn.execute(text(f"""
            SELECT md5(coalesce(string_agg(({expresion})::text, '|'
                ORDER BY m.id), '')) FROM movimientos_kardex m
        """)).scalar_one(),
        conn.execute(text("""
            SELECT md5(coalesce(string_agg(to_jsonb(a)::text, '|'
                ORDER BY a.articulo_id), '')) FROM apertura_inventario a
        """)).scalar_one(),
        conn.execute(text("""
            SELECT md5(coalesce(string_agg(to_jsonb(e)::text, '|'
                ORDER BY e.activo_id, e.area_id), '')) FROM existencia e
        """)).scalar_one(),
        conn.execute(text("SELECT count(*) FROM custodia_externa")).scalar_one(),
        conn.execute(text("SELECT count(*) FROM evento_custodia_externa")).scalar_one(),
    )


def migrar(entorno, destino):
    accion = "upgrade" if destino == NUEVA else "downgrade"
    subprocess.run([sys.executable, "-m", "alembic", accion, destino],
                   env=entorno, check=True)


def comprobar_nuevo(conn, original):
    assert version(conn) == NUEVA and estado(conn, migrada=True) == original
    for campo in CAMPOS:
        assert conn.execute(text(f"SELECT count(*) FROM movimientos_kardex WHERE {campo} IS NOT NULL")).scalar_one() == 0


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
            qa_antes = estado(conn, migrada=True)
            comprobar_nuevo(conn, qa_antes)
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
        print("Migración y reversión verificadas en QA; principal sin cambios")
        return

    marca = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    respaldo = Path("backups") / f"ajustes_{marca}.dump"
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
