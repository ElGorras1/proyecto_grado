"""C03: ensayo reversible y migración sin habilitar áreas ni confirmar equivalencias.

python -m scripts.preparar_administracion_areas --respaldo backups/respaldo_FECHA [--aplicar]
"""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from app.db.session import engine
from scripts.respaldo_recuperacion import verificar_paquete, secuencias

BACKEND = Path(__file__).resolve().parents[1]
ANTERIOR, NUEVA = "s94e53afb168", "t05f64b0c279"
MODULO = "migrations.versions.t05f64b0c279_administracion_areas"


def estado(conn):
    tablas = {}
    for nombre in inspect(conn).get_table_names():
        if nombre == "alembic_version":
            continue
        expresion = "to_jsonb(t)" + (" - 'activa'" if nombre == "sinonimos_area" else "")
        quoted = conn.dialect.identifier_preparer.quote(nombre)
        filas = conn.scalars(text(f"SELECT ({expresion})::text FROM {quoted} t")).all()
        tablas[nombre] = dict(filas=len(filas), sha256=hashlib.sha256("\n".join(sorted(filas)).encode()).hexdigest())
    return dict(tablas=tablas, secuencias=secuencias(conn))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--respaldo", required=True, type=Path)
    p.add_argument("--aplicar", action="store_true")
    args = p.parse_args()
    respaldo = args.respaldo.resolve(strict=True)
    if not respaldo.is_relative_to((BACKEND / "backups").resolve()):
        raise RuntimeError("Respaldo fuera de la carpeta del proyecto")
    verificar_paquete(respaldo)
    ver = json.loads((respaldo / "verificacion.json").read_text(encoding="utf-8"))
    nombre = ver["base_restaurada"]
    if ver["resultado"] != "VERIFICADO" or not re.fullmatch(r"activos_recuperacion_qa_[a-z0-9]+", nombre):
        raise RuntimeError("Falta una restauración QA verificada")
    qa = create_engine(engine.url.set(database=nombre))
    with engine.connect() as conn:
        if conn.scalar(text("SELECT version_num FROM alembic_version")) != ANTERIOR:
            raise RuntimeError("La revisión institucional no coincide con la previa")
        antes = estado(conn)
    with qa.connect() as conn:
        version_qa = conn.scalar(text("SELECT version_num FROM alembic_version"))
        antes_qa = estado(conn)
        if version_qa not in (ANTERIOR, NUEVA) or antes_qa["tablas"] != antes["tablas"]:
            raise RuntimeError("La copia restaurada difiere de los datos actuales")
    pasos = [("upgrade", NUEVA), ("downgrade", ANTERIOR), ("upgrade", NUEVA)]
    if version_qa == NUEVA:
        pasos.insert(0, ("downgrade", ANTERIOR))
    env = os.environ.copy()
    env["DATABASE_URL"] = qa.url.render_as_string(hide_password=False)
    for accion, destino in pasos:
        r = subprocess.run([sys.executable, "-m", "alembic", accion, destino], cwd=BACKEND,
                           env=env, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError("Falló el ensayo Alembic: " + r.stderr[-2000:])
        with qa.connect() as conn:
            assert estado(conn) == antes_qa, "La migración cambió datos preexistentes"
    reporte = dict(tarea="C03", respaldo=respaldo.name, base_qa=nombre, migracion=NUEVA,
                   ensayo="upgrade-downgrade-upgrade", datos_preexistentes_conservados=True,
                   areas_habilitadas=0, equivalencias_confirmadas=0, aplicado=False)
    if args.aplicar:
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL lock_timeout='5s'"))
            conn.execute(text("SET LOCAL statement_timeout='60s'"))
            nombres = ", ".join(conn.dialect.identifier_preparer.quote(t) for t in sorted(antes["tablas"]))
            conn.execute(text("LOCK TABLE " + nombres + " IN SHARE MODE"))
            if estado(conn) != antes:
                raise RuntimeError("La base cambió; prepara un respaldo nuevo")
            with Operations.context(MigrationContext.configure(conn)):
                importlib.import_module(MODULO).upgrade()
            cambio = conn.execute(text("UPDATE alembic_version SET version_num=:n WHERE version_num=:a"),
                                  dict(n=NUEVA, a=ANTERIOR))
            assert cambio.rowcount == 1 and estado(conn) == antes
            assert conn.scalar(text("SELECT count(*) FROM sinonimos_area WHERE activa=FALSE")) == 0
        reporte["aplicado"] = True
    out = BACKEND / "backups/c03_areas_catalogos_20261029/migracion.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(reporte, ensure_ascii=False))


if __name__ == "__main__":
    main()
