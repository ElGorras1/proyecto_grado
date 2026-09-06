import pytest
from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password
from app.models.auditoria import AuditoriaSistema
from app.models.rol import Rol
from app.models.usuario import Usuario


@pytest.fixture(autouse=True)
def reset_limiter():
    limiter.reset()
    yield
    limiter.reset()


def get_auth_headers(usuario: Usuario) -> dict[str, str]:
    token = create_access_token(
        subject=usuario.id,
        extra_claims={"rol": usuario.rol.nombre},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def usuario_auditor(db_session):
    rol = db_session.query(Rol).filter(Rol.nombre == "Auditor").first()
    if not rol:
        rol = Rol(nombre="Auditor", descripcion="Rol auditor", estado="activo")
        db_session.add(rol)
        db_session.commit()

    usuario = Usuario(
        rol_id=rol.id,
        nombre="Auditor de prueba",
        email="auditor_usuarios@test.com",
        password_hash=hash_password("Password123!"),
        estado="activo",
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


# ── Test 1: Crear usuario como Administrador → 200/201, no expone password_hash ──
def test_crear_usuario_como_administrador_201_sin_password_hash(client, db_session, usuario_admin):
    headers = get_auth_headers(usuario_admin)

    rol_op = db_session.query(Rol).filter(Rol.nombre == "Operador").first()
    if not rol_op:
        rol_op = Rol(nombre="Operador", descripcion="Rol operador", estado="activo")
        db_session.add(rol_op)
        db_session.commit()

    nuevo_payload = {
        "nombre": "Carlos Perez",
        "email": "carlos@test.com",
        "password": "PasswordSegura123!",
        "rol_id": rol_op.id,
    }
    resp = client.post("/api/v1/usuarios", json=nuevo_payload, headers=headers)
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data["nombre"] == "Carlos Perez"
    assert data["email"] == "carlos@test.com"
    assert data["rol"] == "Operador"
    assert data["estado"] == "activo"
    assert "password_hash" not in data
    assert "password" not in data

    # Verificar registro en auditoria
    evento = (
        db_session.query(AuditoriaSistema)
        .filter(
            AuditoriaSistema.accion == "crear_usuario",
            AuditoriaSistema.recurso_id == data["id"],
        )
        .first()
    )
    assert evento is not None
    assert evento.resultado == "exito"


# ── Test 2: Crear usuario con email duplicado → 409 ──
def test_crear_usuario_email_duplicado_409(client, usuario_admin):
    headers = get_auth_headers(usuario_admin)

    payload = {
        "nombre": "Otro Admin",
        "email": usuario_admin.email,
        "password": "Password123!",
        "rol_id": usuario_admin.rol_id,
    }
    resp = client.post("/api/v1/usuarios", json=payload, headers=headers)
    assert resp.status_code == 409
    assert "El email ya está registrado" in resp.json()["detail"]


# ── Test 3: Crear/editar/listar como Operador o Auditor → 403 ──
def test_operador_y_auditor_reciben_403_en_usuarios(
    client, usuario_operador, usuario_auditor, usuario_admin
):
    headers_operador = get_auth_headers(usuario_operador)
    headers_auditor = get_auth_headers(usuario_auditor)

    for headers in (headers_operador, headers_auditor):
        # Listar
        resp_get = client.get("/api/v1/usuarios", headers=headers)
        assert resp_get.status_code == 403

        # Crear
        resp_post = client.post(
            "/api/v1/usuarios",
            json={
                "nombre": "Test 403",
                "email": "test403@test.com",
                "password": "Password123!",
                "rol_id": usuario_operador.rol_id,
            },
            headers=headers,
        )
        assert resp_post.status_code == 403

        # Editar
        resp_put = client.put(
            f"/api/v1/usuarios/{usuario_operador.id}",
            json={"nombre": "Nuevo Nombre"},
            headers=headers,
        )
        assert resp_put.status_code == 403


# ── Test 4: Sin token → 401 ──
def test_endpoints_usuarios_sin_token_401(client, usuario_admin):
    assert client.get("/api/v1/usuarios").status_code == 401
    assert client.get(f"/api/v1/usuarios/{usuario_admin.id}").status_code == 401
    assert client.post("/api/v1/usuarios", json={}).status_code == 401
    assert client.put(f"/api/v1/usuarios/{usuario_admin.id}", json={}).status_code == 401
    assert client.patch(f"/api/v1/usuarios/{usuario_admin.id}/desactivar").status_code == 401
    assert client.patch(f"/api/v1/usuarios/{usuario_admin.id}/reactivar").status_code == 401
    assert client.post(f"/api/v1/usuarios/{usuario_admin.id}/resetear-password", json={}).status_code == 401


# ── Test 5: Un Administrador intenta desactivarse a sí mismo → 400 ──
def test_admin_no_puede_desactivarse_a_si_mismo_400(client, usuario_admin):
    headers = get_auth_headers(usuario_admin)
    resp = client.patch(f"/api/v1/usuarios/{usuario_admin.id}/desactivar", headers=headers)
    assert resp.status_code == 400
    assert "propia cuenta" in resp.json()["detail"]


# ── Test 6: Desactivar al único Administrador activo restante → 400 ──
def test_no_puede_desactivar_ultimo_admin_activo_400(client, db_session, usuario_admin):
    # usuario_admin es actualmente el ÚNICO Administrador activo en la base de datos (count = 1).
    # Simulamos a otro Administrador autenticado intentando desactivar al único admin del sistema.
    admin_llamador = Usuario(
        id=9999,
        rol_id=usuario_admin.rol_id,
        nombre="Admin Llamador",
        email="llamador@test.com",
        password_hash="hash",
        estado="activo",
        rol=usuario_admin.rol,
    )
    client.app.dependency_overrides[get_current_user] = lambda: admin_llamador
    try:
        resp = client.patch(f"/api/v1/usuarios/{usuario_admin.id}/desactivar")
        assert resp.status_code == 400
        assert "último Administrador" in resp.json()["detail"]
    finally:
        client.app.dependency_overrides.pop(get_current_user, None)


# ── Test 7: Resetear contraseña y luego hacer login con la nueva contraseña → 200 ──
def test_resetear_password_y_login_nuevo_password_200(client, db_session, usuario_admin, usuario_operador):
    headers_admin = get_auth_headers(usuario_admin)

    nueva_pass = "NuevaClaveSuperSegura999!"
    resp = client.post(
        f"/api/v1/usuarios/{usuario_operador.id}/resetear-password",
        json={"password_nuevo": nueva_pass},
        headers=headers_admin,
    )
    assert resp.status_code == 200
    assert "mensaje" in resp.json()

    # Login con la clave anterior debe fallar (401)
    resp_vieja = client.post(
        "/api/v1/auth/login",
        json={"email": usuario_operador.email, "password": "Password123!"},
    )
    assert resp_vieja.status_code == 401

    # Login con la nueva clave debe ser exitoso (200)
    resp_nueva = client.post(
        "/api/v1/auth/login",
        json={"email": usuario_operador.email, "password": nueva_pass},
    )
    assert resp_nueva.status_code == 200
    assert "access_token" in resp_nueva.json()


# ── Test 8: Editar usuario con éxito y validación de email duplicado ──
def test_editar_usuario_exito_y_duplicado(client, usuario_admin, usuario_operador):
    headers = get_auth_headers(usuario_admin)

    # Actualizar nombre
    resp_edit = client.put(
        f"/api/v1/usuarios/{usuario_operador.id}",
        json={"nombre": "Operador Actualizado"},
        headers=headers,
    )
    assert resp_edit.status_code == 200
    assert resp_edit.json()["nombre"] == "Operador Actualizado"

    # Intentar actualizar con el email de admin -> 409
    resp_dup = client.put(
        f"/api/v1/usuarios/{usuario_operador.id}",
        json={"email": usuario_admin.email},
        headers=headers,
    )
    assert resp_dup.status_code == 409


# ── Test 9: Reactivar usuario y listar con filtros ──
def test_reactivar_usuario_y_listar_con_filtros(client, db_session, usuario_admin, usuario_operador):
    headers = get_auth_headers(usuario_admin)

    # Desactivar operador
    resp_desact = client.patch(
        f"/api/v1/usuarios/{usuario_operador.id}/desactivar",
        headers=headers,
    )
    assert resp_desact.status_code == 200
    assert resp_desact.json()["estado"] == "baja"

    # Listar con filtro estado=baja
    resp_list_baja = client.get("/api/v1/usuarios?estado=baja", headers=headers)
    assert resp_list_baja.status_code == 200
    assert any(u["id"] == usuario_operador.id for u in resp_list_baja.json())

    # Reactivar operador
    resp_react = client.patch(
        f"/api/v1/usuarios/{usuario_operador.id}/reactivar",
        headers=headers,
    )
    assert resp_react.status_code == 200
    assert resp_react.json()["estado"] == "activo"

    # Listar roles
    resp_roles = client.get("/api/v1/usuarios/roles", headers=headers)
    assert resp_roles.status_code == 200
    assert len(resp_roles.json()) >= 1
