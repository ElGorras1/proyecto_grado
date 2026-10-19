"""Ensaya la migración en un respaldo restaurado y conserva cada fila previa."""

import argparse
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

from alembic.migration import MigrationContext
from alembic.operations import Operations
from app.db.session import engine
from scripts.respaldo_recuperacion import escribir, estado, verificar_paquete

ANTERIOR = "n49e15fa0d73"
NUEVA = "o50a19cb7d24"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("respaldo", type=Path)
    args = parser.parse_args()
    carpeta = args.respaldo.resolve(strict=True)
    manifiesto = verificar_paquete(carpeta)
    verificacion = json.loads((carpeta / "verificacion.json").read_text(encoding="utf-8"))
    nombre = verificacion["base_restaurada"]
    if not nombre.startswith("activos_recuperacion_qa_") or nombre == engine.url.database:
        raise RuntimeError("El ensayo requiere la copia aislada del respaldo")
    copia = create_engine(engine.url.set(database=nombre))
    base = manifiesto["base"]
    tablas = {k: v for k, v in base["tablas"].items() if k != "alembic_version"}
    env = os.environ.copy()
    env["DATABASE_URL"] = copia.url.render_as_string(hide_password=False)
    with copia.connect() as conn:
        assert (
            conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == ANTERIOR
        )
    for accion, destino in [("upgrade", NUEVA), ("downgrade", ANTERIOR), ("upgrade", NUEVA)]:
        subprocess.run([sys.executable, "-m", "alembic", accion, destino], env=env, check=True)
        with copia.connect() as conn:
            posterior = estado(conn)
            assert {
                k: v for k, v in posterior["tablas"].items() if k != "alembic_version"
            } == tablas
            assert posterior["secuencias"] == base["secuencias"]
    revision = importlib.import_module("migrations.versions.o50a19cb7d24_tandas_adicionales")
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL lock_timeout='5s'"))
        conn.execute(text("SET LOCAL statement_timeout='60s'"))
        nombres = ", ".join(
            conn.dialect.identifier_preparer.quote(t) for t in sorted(base["tablas"])
        )
        conn.execute(text("LOCK TABLE " + nombres + " IN SHARE MODE"))
        if estado(conn) != base:
            raise RuntimeError("La base cambió desde el respaldo; crea uno nuevo")
        with Operations.context(MigrationContext.configure(conn)):
            revision.upgrade()
        cambio = conn.execute(
            text("UPDATE alembic_version SET version_num=:n WHERE version_num=:a"),
            {"n": NUEVA, "a": ANTERIOR},
        )
        assert cambio.rowcount == 1
        posterior = estado(conn)
        assert {k: v for k, v in posterior["tablas"].items() if k != "alembic_version"} == tablas
        assert posterior["secuencias"] == base["secuencias"]
    reporte = dict(
        migracion=NUEVA,
        ensayo="upgrade-downgrade-upgrade",
        tablas_conservadas=len(tablas),
        secuencias_conservadas=True,
        aplicado=True,
    )
    escribir(carpeta / "tandas_adicionales.json", reporte)
    print(json.dumps(reporte))
    copia.dispose()


if __name__ == "__main__":
    main()
