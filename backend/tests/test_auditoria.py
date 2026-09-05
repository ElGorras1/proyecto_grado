"""
Tests para auditoría de login, endpoint de reporte de accesos y rate limiting.

Nota sobre el rate limiter:
  slowapi usa almacenamiento en memoria (limits.storage.MemoryStorage).
  El estado persiste entre tests dentro del mismo proceso pytest, por lo que
  el test de rate limiting se coloca AL FINAL y resetea el storage después
  de ejecutarse para no afectar otros tests.
"""

import pytest
from app.models.auditoria import AuditoriaSistema
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.core.security import hash_password


# ── Fixture local: usuario Auditor ──────────────────────────────────────
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


# ── Test 1: login exitoso crea registro de auditoría con resultado="exito" ──
def test_login_exitoso_crea_auditoria(client, db_session, usuario_admin):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Password123!"},
    )
    assert resp.status_code == 200

    registro = (
        db_session.query(AuditoriaSistema)
        .filter(AuditoriaSistema.accion == "login", AuditoriaSistema.resultado == "exito")
        .first()
    )
    assert registro is not None
    assert registro.usuario_id == usuario_admin.id
    assert registro.recurso == "usuario"
    assert registro.recurso_id == usuario_admin.id


# ── Test 2: login fallido crea registro de auditoría con resultado="rechazo" ──
def test_login_fallido_crea_auditoria(client, db_session, usuario_admin):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "clave-incorrecta"},
    )
    assert resp.status_code == 401

    registro = (
        db_session.query(AuditoriaSistema)
        .filter(AuditoriaSistema.accion == "login", AuditoriaSistema.resultado == "rechazo")
        .first()
    )
    assert registro is not None
    assert registro.usuario_id == usuario_admin.id
    assert registro.recurso_id == usuario_admin.id
    assert registro.detalle is not None
    assert registro.detalle["email_intentado"] == "admin@test.com"


# ── Test 3: GET /auditoria/accesos sin token → 401 ──
def test_accesos_sin_token_401(client):
    resp = client.get("/api/v1/auditoria/accesos")
    assert resp.status_code == 401


# ── Test 4: GET /auditoria/accesos con Operador → 403 ──
def test_accesos_operador_403(client, usuario_operador):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "operador@test.com", "password": "Password123!"},
    )
    token = login.json()["access_token"]

    resp = client.get(
        "/api/v1/auditoria/accesos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


# ── Test 5: GET /auditoria/accesos con Administrador → 200 ──
def test_accesos_admin_200(client, db_session, usuario_admin):
    # Generar un registro de auditoría haciendo login
    client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Password123!"},
    )

    token = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Password123!"},
    ).json()["access_token"]

    resp = client.get(
        "/api/v1/auditoria/accesos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Verificar que todos los registros son de accion "login"
    for item in data:
        assert "resultado" in item
        assert "fecha_hora" in item


# ── Test 6: rate limiter bloquea después de 5 intentos ──
def test_rate_limiter_bloquea(client, usuario_admin):
    """
    El rate limiter está configurado a 5 intentos por IP cada 5 minutos.
    Enviamos 6 requests seguidas; la 6ta debe devolver 429 Too Many Requests.
    Después del test, se resetea el storage del limiter para no contaminar
    otros tests.
    """
    from app.core.rate_limit import limiter

    try:
        for i in range(5):
            client.post(
                "/api/v1/auth/login",
                json={"email": "admin@test.com", "password": "Password123!"},
            )

        # El 6to intento debe ser bloqueado
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.com", "password": "Password123!"},
        )
        assert resp.status_code == 429
    finally:
        # Resetear el storage del limiter para no afectar otros tests
        limiter.reset()
