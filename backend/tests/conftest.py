import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import Base, get_db
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.core.security import hash_password

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
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
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


@pytest.fixture
def usuario_auditor(db_session):
    rol = Rol(nombre="Auditor", descripcion="Rol auditor", estado="activo")
    db_session.add(rol)
    db_session.commit()

    usuario = Usuario(
        rol_id=rol.id,
        nombre="Auditor de prueba",
        email="auditor@test.com",
        password_hash=hash_password("Password123!"),
        estado="activo",
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario
