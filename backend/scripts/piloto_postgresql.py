"""Recorridos con PostgreSQL real, solo en una base nueva y marcada como QA."""

import json
import hashlib
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
import xml.etree.ElementTree as ET
from alembic.config import Config
from alembic.script import ScriptDirectory

from sqlalchemy import create_engine, text

from app.db.session import engine
from scripts.verificar_respaldo_actual import snapshot_db
from scripts.respaldo_recuperacion import secuencias

BACKEND = Path(__file__).resolve().parents[1]


def estado_institucional():
    with engine.connect() as conn:
        consecutivos = secuencias(conn)
    archivos = {}
    for nombre in ("storage", ".analytics", ".analytics_operativa"):
        for p in sorted((BACKEND / nombre).rglob("*")):
            if p.is_file():
                if not p.resolve().is_relative_to((BACKEND / nombre).resolve()):
                    raise RuntimeError("Archivo fuera de la raíz del piloto")
                archivos[p.relative_to(BACKEND).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return dict(tablas=snapshot_db(engine), secuencias=consecutivos, archivos=archivos)


def main():
    marca = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    nombre = "activos_piloto_qa_" + marca.lower()
    destino = BACKEND / "backups" / ("piloto_" + marca)
    destino.mkdir(parents=True, exist_ok=False)
    original = estado_institucional()
    head = ScriptDirectory.from_config(Config(str(BACKEND / "alembic.ini"))).get_current_head()
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
    subprocess.run([sys.executable, "-m", "scripts.inicializar_esquema"], cwd=BACKEND, env=env, check=True)
    rechazado = subprocess.run(
        [sys.executable, "-m", "scripts.inicializar_esquema"],
        env=env,
        cwd=BACKEND,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if rechazado.returncode == 0:
        raise RuntimeError("La inicialización no rechazó una base con tablas")
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env, check=True)
    casos = [
        "tests/test_auditoria_integral.py",
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
        "tests/test_administracion_areas.py",
        "tests/test_cierre_documental.py",
        "tests/test_cobertura.py",
        "tests/test_rectificaciones_logisticas.py",
        "tests/test_preparacion_inventario.py",
        "tests/test_circuito_piloto.py",
        "tests/test_validacion_independiente.py",
        "tests/test_particiones_articulo.py",
        "tests/test_resumen_gestiones.py",
        "tests/test_exportacion_analitica.py",
        "tests/test_reportes.py",
        "tests/test_entrega_tecnica.py",
        "tests/test_revision_funcional.py",
        "tests/test_documentos_operativos.py",
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
            cwd=BACKEND,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    posterior = estado_institucional()
    cambios = sorted(k for k in original["tablas"].keys() | posterior["tablas"].keys()
                     if original["tablas"].get(k) != posterior["tablas"].get(k))
    secuencias_intactas = original["secuencias"] == posterior["secuencias"]
    archivos_intactos = original["archivos"] == posterior["archivos"]
    intacto = not cambios and secuencias_intactas and archivos_intactos
    xml = ET.parse(destino / "resultados.xml")
    suites = xml.findall(".//testsuite")
    estadisticas = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    estadisticas["aprobadas"] = estadisticas["tests"] - estadisticas["failures"] - estadisticas["errors"] - estadisticas["skipped"]
    circuito = None
    for propiedad in xml.findall(".//property"):
        if propiedad.get("name") == "circuito_c05":
            circuito = json.loads(propiedad.get("value"))
    if circuito:
        (destino / "circuito.json").write_text(json.dumps(circuito, indent=2, ensure_ascii=False), encoding="utf-8")
    reporte = dict(
        base_qa=nombre,
        esquema="Baseline congelado n49 y Alembic " + head,
        inicializacion_sobre_tablas_existentes="RECHAZADA",
        codigo_salida=resultado.returncode,
        base_institucional_intacta=intacto,
        tablas_modificadas=cambios,
        secuencias_institucionales_intactas=secuencias_intactas,
        archivos_privados_intactos=archivos_intactos,
        archivos_comparados=len(original["archivos"]),
        resultados=estadisticas,
        circuito_completo_verificado=circuito is not None and circuito["cierre_reapertura_y_versionado"] == "APROBADO",
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
