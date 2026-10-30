"""C02: ensaya una migración aditiva en un respaldo restaurado y la aplica sin confirmar datos.

python -m scripts.preparar_cierre_documental --respaldo backups/respaldo_FECHA [--aplicar]
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
ANTERIOR, NUEVA = "r83d42fea057", "s94e53afb168"
MODULO = "migrations.versions.s94e53afb168_cierre_documental"
NUEVOS = ("cierre_movimiento_id", "cierre_huella_fuente", "cierre_snapshot")


def estado(conn):
    salida = {}
    for tabla in inspect(conn).get_table_names():
        if tabla == "alembic_version":
            continue
        expresion = "to_jsonb(t)"
        if tabla == "cobertura_articulo":
            expresion += "".join(" - '" + c + "'" for c in NUEVOS)
        quoted = conn.dialect.identifier_preparer.quote(tabla)
        filas = conn.scalars(text(f"SELECT ({expresion})::text FROM {quoted} t")).all()
        salida[tabla] = dict(filas=len(filas), sha256=hashlib.sha256("\n".join(sorted(filas)).encode()).hexdigest())
    return dict(tablas=salida, secuencias=secuencias(conn))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--respaldo", type=Path, required=True)
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    respaldo = args.respaldo.resolve(strict=True)
    if not respaldo.is_relative_to((BACKEND / "backups").resolve()):
        raise RuntimeError("Respaldo fuera de la carpeta del proyecto")
    verificar_paquete(respaldo)
    verificacion = json.loads((respaldo / "verificacion.json").read_text(encoding="utf-8"))
    nombre = verificacion["base_restaurada"]
    if verificacion["resultado"] != "VERIFICADO" or not re.fullmatch(r"activos_recuperacion_qa_[a-z0-9]+", nombre):
        raise RuntimeError("Se requiere una restauración QA verificada")
    qa = create_engine(engine.url.set(database=nombre))
    out = BACKEND / "backups/c02_cierre_documental_20261029"
    out.mkdir(exist_ok=True)
    with engine.connect() as conn:
        version_real = conn.scalar(text("SELECT version_num FROM alembic_version"))
        if version_real != ANTERIOR:
            raise RuntimeError("La base institucional no está en la revisión previa esperada")
        antes = estado(conn)
    with qa.connect() as conn:
        version_qa = conn.scalar(text("SELECT version_num FROM alembic_version"))
        antes_qa = estado(conn)
        if version_qa not in (ANTERIOR, NUEVA) or antes_qa["tablas"] != antes["tablas"]:
            raise RuntimeError("La copia restaurada difiere del estado actual")
    entorno = os.environ.copy()
    entorno["DATABASE_URL"] = qa.url.render_as_string(hide_password=False)
    pasos = [("upgrade", NUEVA), ("downgrade", ANTERIOR), ("upgrade", NUEVA)]
    if version_qa == NUEVA:
        pasos.insert(0, ("downgrade", ANTERIOR))
    for accion, destino in pasos:
        resultado = subprocess.run([sys.executable, "-m", "alembic", accion, destino],
                                  cwd=BACKEND, env=entorno, capture_output=True, text=True)
        if resultado.returncode:
            raise RuntimeError("Falló el ensayo Alembic: " + resultado.stderr[-2000:])
        with qa.connect() as conn:
            assert estado(conn) == antes_qa, "La migración alteró datos preexistentes"
    reporte = dict(tarea="C02", respaldo=respaldo.name, base_qa=nombre, migracion=NUEVA,
                   ensayo="upgrade-downgrade-upgrade", datos_preexistentes_conservados=True,
                   aprobaciones_creadas=0, aplicado=False)
    if args.aplicar:
        revision = importlib.import_module(MODULO)
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL lock_timeout='5s'"))
            conn.execute(text("SET LOCAL statement_timeout='60s'"))
            tablas = ", ".join(conn.dialect.identifier_preparer.quote(t) for t in sorted(antes["tablas"]))
            conn.execute(text("LOCK TABLE " + tablas + " IN SHARE MODE"))
            if estado(conn) != antes:
                raise RuntimeError("La base cambió durante el ensayo; se requiere un respaldo nuevo")
            with Operations.context(MigrationContext.configure(conn)):
                revision.upgrade()
            cambio = conn.execute(text("UPDATE alembic_version SET version_num=:n WHERE version_num=:a"),
                                  dict(n=NUEVA, a=ANTERIOR))
            assert cambio.rowcount == 1
            assert estado(conn) == antes, "La migración alteró datos preexistentes"
        reporte["aplicado"] = True
    (out / "migracion.json").write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(reporte, ensure_ascii=False))
    qa.dispose()


if __name__ == "__main__":
    main()
