"""Ensaya el esquema y conserva avisos previos sin inventar revisiones."""
import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import app.models
from app.db.session import engine
from app.models.control_alertas import CasoControl, RevisionControl
from app.services.control_alertas import incorporar_avisos_guardados, ORIGENES

ANTERIOR = "l27b9c3e8d51"
NUEVA = "m38c0d4f9e62"
QA = "activos_estado_qa_20261008t044004z"
TABLAS = ("movimientos_kardex", "apertura_inventario", "existencia",
          "custodia_externa", "evento_custodia_externa", "transferencia_area")

def estado(con):
    return {t: tuple(con.execute(text(
        f"SELECT count(*), md5(coalesce(string_agg(to_jsonb(t)::text, '|' ORDER BY to_jsonb(t)::text), '')) FROM {t} t"
    )).one()) for t in TABLAS}

def version(con):
    return con.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

def migrar(env, destino):
    subprocess.run([sys.executable, "-m", "alembic", "upgrade" if destino == NUEVA else "downgrade", destino],
                   env=env, check=True)

def incorporar(destino):
    with Session(destino) as db:
        creados = incorporar_avisos_guardados(db)
        db.commit()
        total = db.query(CasoControl).count()
        esperados = sum(sum(1 for f in db.query(m).filter(m.alertas_control.isnot(None)) if f.alertas_control
            and (clase != "MOVIMIENTO" or f.lote_id is None)) for clase, (m, _) in ORIGENES.items())
        assert total == esperados, "El conteo de casos no coincide con las operaciones alertadas"
        assert incorporar_avisos_guardados(db) == 0, "La incorporación duplicaría casos"
        assert db.query(RevisionControl).count() == 0, "No se crean revisiones humanas automáticas"
        return creados, total

def comprobar(destino, original):
    with destino.connect() as con:
        assert version(con) == NUEVA and estado(con) == original, "Cambió el inventario durante la migración"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    url = engine.url
    assert url.database != QA
    qa = create_engine(url.set(database=QA))
    with engine.connect() as con:
        assert version(con) == ANTERIOR, "La principal debe estar en la revisión anterior"
        original = estado(con)
    env_qa = os.environ.copy()
    env_qa["DATABASE_URL"] = url.set(database=QA).render_as_string(hide_password=False)
    with qa.connect() as con:
        qa_version = version(con)
        assert qa_version in (ANTERIOR, NUEVA)
        antes = estado(con)
        if qa_version == NUEVA:
            assert con.execute(text("SELECT count(*) FROM revision_control")).scalar_one() == 0, "QA contiene revisiones; utiliza otra copia para ensayar reversión"
    if qa_version == NUEVA:
        migrar(env_qa, ANTERIOR)
    migrar(env_qa, NUEVA)
    incorporar(qa)
    comprobar(qa, antes)
    migrar(env_qa, ANTERIOR)
    with qa.connect() as con:
        assert version(con) == ANTERIOR and estado(con) == antes
    migrar(env_qa, NUEVA)
    incorporar(qa)
    comprobar(qa, antes)
    if not args.aplicar:
        print("Avance, reversión e incorporación de avisos verificados en QA; principal sin cambios")
        return
    pg = Path(os.environ.get("POSTGRES_BIN", r"C:\Program Files\PostgreSQL\18\bin"))
    respaldo = Path("backups") / f"bandeja_alertas_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.dump"
    respaldo.parent.mkdir(exist_ok=True)
    env_pg = os.environ.copy()
    env_pg["PGPASSWORD"] = url.password or ""
    conexion = ["-h", url.host or "localhost", "-p", str(url.port or 5432), "-U", url.username or "postgres"]
    subprocess.run([str(pg / "pg_dump.exe"), *conexion, "-Fc", "-f", str(respaldo), url.database], env=env_pg, check=True)
    subprocess.run([str(pg / "pg_restore.exe"), "-l", str(respaldo)], env=env_pg, stdout=subprocess.DEVNULL, check=True)
    with engine.connect() as con:
        assert version(con) == ANTERIOR and estado(con) == original
    migrar(os.environ.copy(), NUEVA)
    creados, total = incorporar(engine)
    comprobar(engine, original)
    print(f"Principal migrada: {original['movimientos_kardex'][0]} movimientos conservados, {total} casos ({creados} incorporados), cero revisiones automáticas; respaldo: {respaldo.resolve()}")

if __name__ == "__main__":
    main()
