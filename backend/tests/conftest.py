import os
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import Base, get_db
from app.main import app
from app.models.rol import Rol
from app.models.usuario import Usuario

# Base de datos SQLite en memoria: rápida y aislada, no requiere Postgres
# corriendo para probar la lógica de autenticación/autorización.
# StaticPool es obligatorio aquí: sin él, cada conexión nueva de SQLAlchemy
# abriría una base ":memory:" distinta y vacía, y las tablas creadas en
# una conexión "desaparecerían" al usar otra.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
piloto_url = os.environ.get("PILOTO_DATABASE_URL")
if piloto_url:
    piloto_engine = create_engine(piloto_url)
    if not re.fullmatch(r"activos_piloto_qa_[a-z0-9]+", piloto_engine.url.database or ""):
        raise RuntimeError("El piloto requiere una base QA nueva; se rechaza cualquier otra base")
    with piloto_engine.connect() as conn:
        marca = conn.execute(
            text(
                "SELECT shobj_description(oid, 'pg_database') "
                "FROM pg_database WHERE datname=current_database()"
            )
        ).scalar_one()
        if not os.environ.get("PILOTO_AUTORIZACION") or marca != os.environ["PILOTO_AUTORIZACION"]:
            raise RuntimeError("La base no fue creada para este piloto aislado")
    engine = piloto_engine
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def horario_estable_en_pruebas(monkeypatch):
    # Un cliente de pruebas nunca debe iniciar el trabajador de la instalación real.
    monkeypatch.setattr('app.main.iniciar', lambda: None)
    # Las pruebas generales no dependen de la hora del equipo que ejecuta CI.
    monkeypatch.setattr(settings, "CONTROL_HORA_INICIO", 0)
    monkeypatch.setattr(settings, "CONTROL_HORA_FIN", 24)


@pytest.fixture(scope="function")
def db_session():
    if piloto_url:
        # Solo se limpian fixtures de la base nueva cuya identidad se verificó arriba.
        # El esquema proviene de Alembic y se conserva durante todos los recorridos.
        with engine.begin() as conn:
            tablas = ", ".join(
                conn.dialect.identifier_preparer.quote(t.name)
                for t in Base.metadata.tables.values()
            )
            conn.execute(text("TRUNCATE TABLE " + tablas + " RESTART IDENTITY CASCADE"))
    else:
        Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        if not piloto_url:
            Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def usuario_admin(db_session):
    rol = Rol(nombre="Administrador", descripcion="Rol admin", estado="activo")
    db_session.add(rol)
    db_session.commit()

    usuario = Usuario(
        rol_id=rol.id,
        nombre="Admin de prueba",
        email="admin@test.com",
        password_hash=hash_password("Password123!"),
        estado="activo",
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


@pytest.fixture
def usuario_operador(db_session):
    rol = Rol(nombre="Operador", descripcion="Rol operador", estado="activo")
    db_session.add(rol)
    db_session.commit()

    usuario = Usuario(
        rol_id=rol.id,
        nombre="Operador de prueba",
        email="operador@test.com",
        password_hash=hash_password("Password123!"),
        estado="activo",
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario
