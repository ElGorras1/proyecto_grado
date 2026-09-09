import pytest
from app.core.security import create_access_token
from app.models.activos import CategoriaActivo
from app.models.auditoria import AuditoriaSistema
from app.models.usuario import Usuario


def get_auth_headers(usuario: Usuario) -> dict[str, str]:
    token = create_access_token(
        subject=usuario.id,
        extra_claims={"rol": usuario.rol.nombre},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def categoria_ejemplo(db_session):
    cat = CategoriaActivo(
        nombre="Equipos de Cómputo",
        codigo="CAT-01",
        descripcion="Laptops, servidores y periféricos",
        estado="activo",
    )
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


# ── Test 1: GET sin token → 401 ──
def test_listar_categorias_sin_token_401(client):
    resp = client.get("/api/v1/categorias")
    assert resp.status_code == 401


# ── Test 2: GET abierto a Administrador, Operador y Auditor → 200 ──
def test_listar_categorias_tres_roles_200(client, usuario_admin, usuario_operador, usuario_auditor, categoria_ejemplo):
    for usuario in [usuario_admin, usuario_operador, usuario_auditor]:
        resp = client.get("/api/v1/categorias", headers=get_auth_headers(usuario))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert any(c["nombre"] == "Equipos de Cómputo" for c in data)


# ── Test 3: GET detalle por ID (200 y 404) ──
def test_obtener_categoria_detalle(client, usuario_operador, categoria_ejemplo):
    resp = client.get(f"/api/v1/categorias/{categoria_ejemplo.id}", headers=get_auth_headers(usuario_operador))
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Equipos de Cómputo"

    resp_404 = client.get("/api/v1/categorias/99999", headers=get_auth_headers(usuario_operador))
    assert resp_404.status_code == 404


# ── Test 4: RBAC POST — Solo Administrador (201), Operador y Auditor → 403 ──
def test_rbac_crear_categoria(client, db_session, usuario_admin, usuario_operador, usuario_auditor):
    payload = {"nombre": "Mobiliario", "codigo": "CAT-MOB", "descripcion": "Muebles y escritorios"}

    # Operador -> 403
    resp_op = client.post("/api/v1/categorias", json=payload, headers=get_auth_headers(usuario_operador))
    assert resp_op.status_code == 403

    # Auditor -> 403
    resp_aud = client.post("/api/v1/categorias", json=payload, headers=get_auth_headers(usuario_auditor))
    assert resp_aud.status_code == 403

    # Administrador -> 201
    resp_admin = client.post("/api/v1/categorias", json=payload, headers=get_auth_headers(usuario_admin))
    assert resp_admin.status_code == 201
    data = resp_admin.json()
    assert data["nombre"] == "Mobiliario"
    assert data["codigo"] == "CAT-MOB"

    # Verificar auditoría
    evento = (
        db_session.query(AuditoriaSistema)
        .filter(
            AuditoriaSistema.accion == "crear_categoria_activo",
            AuditoriaSistema.recurso == "categoria_activo",
            AuditoriaSistema.recurso_id == data["id"],
        )
        .first()
    )
    assert evento is not None
    assert evento.resultado == "exito"


# ── Test 5: Validación de duplicados (nombre y código) → 409 ──
def test_crear_categoria_duplicados_409(client, usuario_admin, categoria_ejemplo):
    # Nombre duplicado
    resp_nombre = client.post(
        "/api/v1/categorias",
        json={"nombre": categoria_ejemplo.nombre, "codigo": "CAT-OTRO"},
        headers=get_auth_headers(usuario_admin),
    )
    assert resp_nombre.status_code == 409
    assert "nombre" in resp_nombre.json()["detail"]

    # Código duplicado
    resp_codigo = client.post(
        "/api/v1/categorias",
        json={"nombre": "Otra Categoría", "codigo": categoria_ejemplo.codigo},
        headers=get_auth_headers(usuario_admin),
    )
    assert resp_codigo.status_code == 409
    assert "código" in resp_codigo.json()["detail"]


# ── Test 6: RBAC PUT — Solo Administrador (200), Operador y Auditor → 403 ──
def test_rbac_actualizar_categoria(client, db_session, usuario_admin, usuario_operador, usuario_auditor, categoria_ejemplo):
    payload = {"nombre": "Equipos de Cómputo Actualizados", "descripcion": "Nueva descripción"}

    # Operador -> 403
    resp_op = client.put(f"/api/v1/categorias/{categoria_ejemplo.id}", json=payload, headers=get_auth_headers(usuario_operador))
    assert resp_op.status_code == 403

    # Auditor -> 403
    resp_aud = client.put(f"/api/v1/categorias/{categoria_ejemplo.id}", json=payload, headers=get_auth_headers(usuario_auditor))
    assert resp_aud.status_code == 403

    # Administrador -> 200
    resp_admin = client.put(f"/api/v1/categorias/{categoria_ejemplo.id}", json=payload, headers=get_auth_headers(usuario_admin))
    assert resp_admin.status_code == 200
    assert resp_admin.json()["nombre"] == "Equipos de Cómputo Actualizados"


# ── Test 7: RBAC Desactivar y reactivar — Solo Administrador ──
def test_rbac_desactivar_y_reactivar_categoria(client, db_session, usuario_admin, usuario_operador, usuario_auditor, categoria_ejemplo):
    # Operador -> 403
    resp_op = client.patch(f"/api/v1/categorias/{categoria_ejemplo.id}/desactivar", headers=get_auth_headers(usuario_operador))
    assert resp_op.status_code == 403

    # Auditor -> 403
    resp_aud = client.patch(f"/api/v1/categorias/{categoria_ejemplo.id}/desactivar", headers=get_auth_headers(usuario_auditor))
    assert resp_aud.status_code == 403

    # Admin desactiva -> 200 (estado = 'baja')
    resp_admin_des = client.patch(f"/api/v1/categorias/{categoria_ejemplo.id}/desactivar", headers=get_auth_headers(usuario_admin))
    assert resp_admin_des.status_code == 200
    assert resp_admin_des.json()["estado"] == "baja"

    # Admin reactiva -> 200 (estado = 'activo')
    resp_admin_rea = client.patch(f"/api/v1/categorias/{categoria_ejemplo.id}/reactivar", headers=get_auth_headers(usuario_admin))
    assert resp_admin_rea.status_code == 200
    assert resp_admin_rea.json()["estado"] == "activo"
