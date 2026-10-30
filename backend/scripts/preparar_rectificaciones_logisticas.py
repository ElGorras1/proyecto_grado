"""C04: ensayo de migración en respaldo restaurado y aplicación reconciliada."""
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
ANTERIOR, NUEVA = "t05f64b0c279", "u16a75c1d380"
MODULO = "migrations.versions.u16a75c1d380_rectificaciones_logisticas"


def estado(conn):
    tablas = {}
    for nombre in inspect(conn).get_table_names():
        if nombre in ("alembic_version", "rectificacion_logistica"):
            continue
        expresion = "to_jsonb(t)" + (" - 'cantidad_ajustada'" if nombre == "custodia_externa" else "")
        quoted = conn.dialect.identifier_preparer.quote(nombre)
        filas = conn.scalars(text(f"SELECT ({expresion})::text FROM {quoted} t")).all()
        tablas[nombre] = dict(filas=len(filas), sha256=hashlib.sha256("\n".join(sorted(filas)).encode()).hexdigest())
    return dict(tablas=tablas, secuencias={k:v for k,v in secuencias(conn).items() if k != "rectificacion_logistica_id_seq"})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--respaldo", type=Path, required=True)
    p.add_argument("--aplicar", action="store_true")
    args = p.parse_args()
    respaldo = args.respaldo.resolve(strict=True)
    if not respaldo.is_relative_to((BACKEND / "backups").resolve()):
        raise RuntimeError("Respaldo fuera del proyecto")
    verificar_paquete(respaldo)
    v = json.loads((respaldo / "verificacion.json").read_text(encoding="utf-8"))
    nombre = v["base_restaurada"]
    if v["resultado"] != "VERIFICADO" or not re.fullmatch(r"activos_recuperacion_qa_[a-z0-9]+", nombre):
        raise RuntimeError("Se requiere restauración QA verificada")
    qa = create_engine(engine.url.set(database=nombre))
    with engine.connect() as c:
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == ANTERIOR
        antes = estado(c)
    with qa.connect() as c:
        version = c.scalar(text("SELECT version_num FROM alembic_version"))
        antes_qa = estado(c)
        assert version in (ANTERIOR, NUEVA) and antes_qa["tablas"] == antes["tablas"]
        if version == NUEVA:
            assert c.scalar(text("SELECT count(*) FROM rectificacion_logistica")) == 0
    pasos = [("upgrade", NUEVA), ("downgrade", ANTERIOR), ("upgrade", NUEVA)]
    if version == NUEVA:
        pasos.insert(0, ("downgrade", ANTERIOR))
    env = os.environ.copy()
    env["DATABASE_URL"] = qa.url.render_as_string(hide_password=False)
    for accion, destino in pasos:
        r = subprocess.run([sys.executable, "-m", "alembic", accion, destino], cwd=BACKEND,
                           env=env, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError("Falló el ensayo Alembic: " + r.stderr[-2000:])
        with qa.connect() as c:
            assert estado(c) == antes_qa
    reporte = dict(tarea="C04", migracion=NUEVA, base_qa=nombre, respaldo=respaldo.name,
                   ensayo="upgrade-downgrade-upgrade", datos_preexistentes_conservados=True, aplicado=False)
    if args.aplicar:
        with engine.begin() as c:
            c.execute(text("SET LOCAL lock_timeout='5s'"))
            c.execute(text("SET LOCAL statement_timeout='60s'"))
            tablas = ", ".join(c.dialect.identifier_preparer.quote(t) for t in sorted(antes["tablas"]))
            c.execute(text("LOCK TABLE " + tablas + " IN SHARE MODE"))
            if estado(c) != antes:
                raise RuntimeError("La base cambió desde el respaldo")
            with Operations.context(MigrationContext.configure(c)):
                importlib.import_module(MODULO).upgrade()
            assert c.execute(text("UPDATE alembic_version SET version_num=:n WHERE version_num=:a"),
                             dict(n=NUEVA, a=ANTERIOR)).rowcount == 1
            assert estado(c) == antes
            assert c.scalar(text("SELECT count(*) FROM rectificacion_logistica")) == 0
        reporte["aplicado"] = True
    out = BACKEND / "backups/c04_rectificaciones_20261029/migracion.json"
    out.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(reporte, ensure_ascii=False))


if __name__ == "__main__":
    main()
