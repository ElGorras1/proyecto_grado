"""Instala la migración aditiva tras restaurarla y comprobarla en una copia.

Uso: python -m scripts.preparar_analitica [--aplicar]
Conserva dump completo, ZIP de evidencia, copia PostgreSQL y reconciliación.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from app.db.session import engine


def digest_tablas(conn, tablas):
    resultados = {}
    for nombre in tablas:
        # Nombres exclusivamente de inspector de PostgreSQL; quoted identifier.
        quoted = conn.dialect.identifier_preparer.quote(nombre)
        filas = conn.execute(text(f"SELECT row_to_json(t)::text FROM {quoted} t")).scalars().all()
        resultados[nombre] = {
            "filas": len(filas),
            "sha256": hashlib.sha256("\n".join(sorted(filas)).encode()).hexdigest(),
        }
    return resultados


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--aplicar", action="store_true")
    aplicar = args.parse_args().aplicar
    marca = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    carpeta = Path("backups") / ("analitica_" + marca)
    carpeta.mkdir(parents=True)
    url = engine.url
    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password
    pg = Path(os.environ.get("POSTGRES_BIN", r"C:\Program Files\PostgreSQL\18\bin"))
    conexion = [
        "-h",
        url.host or "localhost",
        "-p",
        str(url.port or 5432),
        "-U",
        url.username or "postgres",
    ]
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        if version != "e04f1b5d2a68":
            raise RuntimeError(
                "La migración debe partir de e04f1b5d2a68; no se aplicó ningún cambio."
            )
    dump = carpeta / "base.dump"
    subprocess.run(
        [str(pg / "pg_dump.exe"), *conexion, "-Fc", "-f", str(dump), url.database],
        env=env,
        check=True,
    )
    manifiesto = []
    with zipfile.ZipFile(carpeta / "evidencia.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(Path("storage").rglob("*")):
            if p.is_file():
                contenido = p.read_bytes()
                z.writestr(p.as_posix(), contenido)
                manifiesto.append(
                    {
                        "ruta": p.as_posix(),
                        "bytes": len(contenido),
                        "sha256": hashlib.sha256(contenido).hexdigest(),
                    }
                )
    with zipfile.ZipFile(carpeta / "evidencia.zip") as z:
        assert z.testzip() is None
    (carpeta / "evidencia.json").write_text(json.dumps(manifiesto, indent=2), encoding="utf-8")
    nombre = "activos_analitica_qa_" + marca.lower()
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{nombre}"'))
    subprocess.run(
        [
            str(pg / "pg_restore.exe"),
            *conexion,
            "--no-owner",
            "--exit-on-error",
            "-d",
            nombre,
            str(dump),
        ],
        env=env,
        check=True,
    )
    copia = create_engine(url.set(database=nombre))
    with copia.connect() as conn:
        tablas = [t for t in inspect(conn).get_table_names() if t != "alembic_version"]
        antes = digest_tablas(conn, tablas)
    entorno = env.copy()
    entorno["DATABASE_URL"] = url.set(database=nombre).render_as_string(hide_password=False)
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], env=entorno, check=True)
    with copia.connect() as conn:
        assert digest_tablas(conn, tablas) == antes, "Diferencias en copia migrada"
    subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "e04f1b5d2a68"], env=entorno, check=True
    )
    with copia.connect() as conn:
        assert digest_tablas(conn, tablas) == antes, "Diferencias después de revertir copia"
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], env=entorno, check=True)
    reporte = {
        "copia": nombre,
        "respaldo": str(dump),
        "evidencias": len(manifiesto),
        "tablas_verificadas": antes,
        "copia_upgrade_downgrade_upgrade": "correcto",
        "aplicado": False,
    }
    if aplicar:
        # Bloqueos compartidos durante la comprobación impiden escrituras concurrentes
        # brevemente; se migra en la MISMA transacción, sin detener cargas/servidor.
        import importlib

        from alembic.migration import MigrationContext
        from alembic.operations import Operations

        revision = importlib.import_module("migrations.versions.f15a2c6e3b79_analitica_historica")
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL lock_timeout = '5s'"))
            conn.execute(text("SET LOCAL statement_timeout = '60s'"))
            names = ", ".join(
                conn.dialect.identifier_preparer.quote(t)
                for t in sorted(tablas + ["alembic_version"])
            )
            conn.execute(text("LOCK TABLE " + names + " IN SHARE MODE"))
            previo = digest_tablas(conn, tablas)
            with Operations.context(MigrationContext.configure(conn)):
                revision.upgrade()
            conn.execute(
                text(
                    
                        "UPDATE alembic_version SET version_num='f15a2c6e3b79' WHERE "
                        "version_num='e04f1b5d2a68'"
                    
                )
            )
            assert digest_tablas(conn, tablas) == previo, "Reconciliación fallida"
        reporte["aplicado"] = True
        reporte["reconciliacion_actual"] = previo
    (carpeta / "verificacion.json").write_text(json.dumps(reporte, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "respaldo": str(carpeta.resolve()),
                "copia": nombre,
                "aplicado": aplicar,
                "evidencias": len(manifiesto),
            }
        )
    )


if __name__ == "__main__":
    main()
