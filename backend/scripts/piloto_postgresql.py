"""Recorridos con PostgreSQL real, solo en una base nueva y marcada como QA."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.db.session import engine
from scripts.verificar_respaldo_actual import snapshot_db

BACKEND = Path(__file__).resolve().parents[1]


def main():
    marca = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    nombre = "activos_piloto_qa_" + marca.lower()
    destino = BACKEND / "backups" / ("piloto_" + marca)
    destino.mkdir(parents=True, exist_ok=False)
    original = snapshot_db(engine)
    marca_segura = "PILOTO_AISLADO_" + str(uuid4())
    admin = create_engine(engine.url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{nombre}"'))
        conn.execute(text(f'COMMENT ON DATABASE "{nombre}" IS :marca'), {"marca": marca_segura})
    admin.dispose()
    env = os.environ.copy()
    env["DATABASE_URL"] = engine.url.set(database=nombre).render_as_string(hide_password=False)
    env["PILOTO_DATABASE_URL"] = env["DATABASE_URL"]
    env["PILOTO_AUTORIZACION"] = marca_segura
    subprocess.run([sys.executable, "-m", "scripts.inicializar_esquema"], env=env, check=True)
    rechazado = subprocess.run(
        [sys.executable, "-m", "scripts.inicializar_esquema"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if rechazado.returncode == 0:
        raise RuntimeError("La inicialización no rechazó una base con tablas")
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], env=env, check=True)
    casos = [
        "tests/test_apertura_inventario.py",
        "tests/test_conciliacion_inicial.py",
        "tests/test_transferencias_area.py",
        "tests/test_custodias_externas.py",
        "tests/test_devoluciones.py",
        "tests/test_ajustes_operativos.py",
        "tests/test_control_alertas.py",
        "tests/test_analitica_operativa.py",
        "tests/test_filtros_gestion.py",
        "tests/test_tandas.py",
        "tests/test_evaluacion_temporal.py",
        "tests/test_cierre_anual.py",
        "tests/test_reporte_institucional.py",
        "tests/test_seguridad_institucional.py",
        "tests/test_inicializacion_admin.py",
        "tests/test_usuarios.py",
    ]
    with (destino / "resultado.log").open("w", encoding="utf-8") as log:
        resultado = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                *casos,
                "-q",
                "--junitxml",
                str(destino / "resultados.xml"),
            ],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    intacto = original == snapshot_db(engine)
    reporte = dict(
        base_qa=nombre,
        esquema="Baseline congelado n49 y Alembic head",
        inicializacion_sobre_tablas_existentes="RECHAZADA",
        codigo_salida=resultado.returncode,
        base_institucional_intacta=intacto,
        pruebas=casos,
        limite="Datos ficticios; no sustituye el piloto con personal y conteos físicos reales.",
    )
    (destino / "verificacion.json").write_text(
        json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(dict(carpeta=str(destino), **reporte), ensure_ascii=False))
    if resultado.returncode or not intacto:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
