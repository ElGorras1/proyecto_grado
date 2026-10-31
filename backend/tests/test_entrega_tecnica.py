"""Regresiones de conexión, migración y respaldo en una instalación nueva."""

import os
import runpy
from contextlib import nullcontext
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import context
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy.engine import make_url
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

from app.core.config import Settings, settings
from app.core.postgres_tools import postgres_tool


def test_conexion_por_parametros_conserva_password_especial():
    secreto = "clave @/:#% con caracteres"
    config = Settings(_env_file=None, DATABASE_URL="", JWT_SECRET_KEY="prueba",
                      POSTGRES_HOST="db", POSTGRES_DB="activos", POSTGRES_USER="app",
                      POSTGRES_PASSWORD=secreto)
    url = make_url(config.DATABASE_URL)
    assert url.password == secreto
    assert (url.host, url.database, url.username) == ("db", "activos", "app")
    assert secreto not in repr(config.POSTGRES_PASSWORD)


def test_conexion_incompleta_no_construye_una_base_por_defecto():
    with pytest.raises(ValidationError, match="Configura DATABASE_URL"):
        Settings(_env_file=None, DATABASE_URL="", JWT_SECRET_KEY="prueba",
                 POSTGRES_HOST="db", POSTGRES_PASSWORD="privada")


def test_migracion_no_interpreta_password_como_interpolacion(monkeypatch):
    url = "postgresql+psycopg2://app:p%40ss%25%2Fword@db/activos"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    recibido = {}
    monkeypatch.setattr(context, "config", config, raising=False)
    monkeypatch.setattr(context, "is_offline_mode", lambda: True)
    monkeypatch.setattr(context, "configure", lambda **kw: recibido.update(kw))
    monkeypatch.setattr(context, "begin_transaction", nullcontext)
    monkeypatch.setattr(context, "run_migrations", lambda: None)
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "migrations/env.py"))
    assert recibido["url"] == url
    assert make_url(recibido["url"]).password == "p@ss%/word"


@pytest.mark.parametrize("nombre", ["pg_dump", "pg_restore"])
def test_cliente_postgres_respeta_directorio_con_espacios(tmp_path, monkeypatch, nombre):
    carpeta = tmp_path / "Cliente PostgreSQL" / "bin"
    carpeta.mkdir(parents=True)
    exe = carpeta / (nombre + (".exe" if os.name == "nt" else ""))
    exe.write_bytes(b"ejecutable ficticio; no se ejecuta")
    monkeypatch.setenv("POSTGRES_BIN", str(carpeta))
    assert postgres_tool(nombre) == exe.resolve()


def test_cliente_postgres_busca_en_path_y_rechaza_override_invalido(tmp_path, monkeypatch):
    from app.core import postgres_tools

    monkeypatch.delenv("POSTGRES_BIN", raising=False)
    monkeypatch.setattr(postgres_tools.shutil, "which", lambda _: str(tmp_path / "pg_dump"))
    assert postgres_tool("pg_dump") == (tmp_path / "pg_dump").resolve()
    monkeypatch.setenv("POSTGRES_BIN", str(tmp_path / "no_existe"))
    with pytest.raises(RuntimeError, match="POSTGRES_BIN"):
        postgres_tool("pg_dump")


def test_rol_aplicacion_puede_operar_pero_no_cambiar_esquema(db_session):
    engine = db_session.get_bind()
    if engine.dialect.name != "postgresql":
        pytest.skip("Requiere el piloto PostgreSQL aislado")
    assert (engine.url.database or "").startswith("activos_piloto_qa_")
    rol = "activos_c07_qa_" + uuid4().hex
    tabla = "c07_default_" + uuid4().hex
    script = Path(__file__).resolve().parents[1] / "init_db/03_app_role.sh"
    sql = script.read_text(encoding="utf-8").split("<<'SQL'\n", 1)[1].rsplit("\nSQL", 1)[0]
    sql = sql.replace("activos_app", rol).replace("activos_db", engine.url.database)
    sql = sql.replace(":'app_password'", ":app_password")
    password = "solo-QA-@%/" + uuid4().hex
    creada = False
    app_engine = None
    try:
        with engine.begin() as conn:
            conn.execute(text(sql), {"app_password": password})
        creada = True
        with engine.begin() as conn:
            conn.execute(text(f'CREATE TABLE "{tabla}" (id integer)'))
        app_engine = create_engine(engine.url.set(username=rol, password=password))
        with app_engine.begin() as conn:
            assert conn.execute(text("SELECT count(*) FROM activo")).scalar_one() >= 0
            conn.execute(text("INSERT INTO area (nombre, estado) VALUES ('Área QA C07', 'activo')"))
            assert conn.execute(text(f'SELECT count(*) FROM "{tabla}"')).scalar_one() == 0
        for sentencia in (f'CREATE TABLE "{tabla}_no_permitida" (id integer)',
                          "TRUNCATE TABLE area", "DELETE FROM alembic_version"):
            with pytest.raises(ProgrammingError):
                with app_engine.begin() as conn:
                    conn.execute(text(sentencia))
    finally:
        if app_engine:
            app_engine.dispose()
        if creada:
            with engine.begin() as conn:
                conn.execute(text(f'DROP TABLE IF EXISTS "{tabla}"'))
                conn.execute(text(f'DROP OWNED BY "{rol}"'))
                conn.execute(text(f'DROP ROLE "{rol}"'))
