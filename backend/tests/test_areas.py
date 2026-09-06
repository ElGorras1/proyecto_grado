import pytest
from app.core.rate_limit import limiter
from app.core.security import create_access_token
from app.models.area import Area
from app.models.auditoria import AuditoriaSistema
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
def area_ejemplo(db_session):
    area = Area(
        nombre="Almacén Central",
        codigo="ALM-01",
        descripcion="Área principal de almacenamiento",
        estado="activo",
    )
    db_session.add(area)
    db_session.commit()
    db_session.refresh(area)
    return area


# ── Test 1: Ver áreas sin token → 401 ──
def test_ver_areas_sin_token_401(client):
    resp = client.get("/api/v1/areas")
    assert resp.status_code == 401


# ── Test 2: Cualquier usuario autenticado (Operador y Admin) puede VER áreas → 200 ──
def test_listar_areas_cualquier_usuario_autenticado_200(client, usuario_operador, usuario_admin, area_ejemplo):
    # Operador
    headers_op = get_auth_headers(usuario_operador)
    resp_op = client.get("/api/v1/areas", headers=headers_op)
    assert resp_op.status_code == 200
    data_op = resp_op.json()
    assert isinstance(data_op, list)
    assert len(data_op) >= 1
    assert any(a["nombre"] == "Almacén Central" for a in data_op)

    # Administrador
    headers_admin = get_auth_headers(usuario_admin)
    resp_admin = client.get("/api/v1/areas", headers=headers_admin)
    assert resp_admin.status_code == 200


# ── Test 3: Detalle de área (GET /areas/{id}) ──
def test_obtener_area_por_id(client, usuario_operador, area_ejemplo):
    headers_op = get_auth_headers(usuario_operador)
    resp = client.get(f"/api/v1/areas/{area_ejemplo.id}", headers=headers_op)
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Almacén Central"

    # 404 si no existe
    resp_404 = client.get("/api/v1/areas/99999", headers=headers_op)
    assert resp_404.status_code == 404


# ── Test 4: Operador NO puede crear, editar ni desactivar áreas → 403 ──
def test_operador_no_puede_modificar_areas_403(client, usuario_operador, area_ejemplo):
    headers_op = get_auth_headers(usuario_operador)

    # Crear -> 403
    resp_post = client.post(
        "/api/v1/areas",
        json={"nombre": "Nueva Área No Autorizada"},
        headers=headers_op,
    )
    assert resp_post.status_code == 403

    # Editar -> 403
    resp_put = client.put(
        f"/api/v1/areas/{area_ejemplo.id}",
        json={"nombre": "Nombre Cambiado"},
        headers=headers_op,
    )
    assert resp_put.status_code == 403

    # Desactivar -> 403
    resp_patch = client.patch(
        f"/api/v1/areas/{area_ejemplo.id}/desactivar",
        headers=headers_op,
    )
    assert resp_patch.status_code == 403


# ── Test 5: Administrador crea área exitosamente → 201 ──
def test_administrador_crea_area_201(client, db_session, usuario_admin):
    headers_admin = get_auth_headers(usuario_admin)

    payload = {
        "nombre": "Tecnología e Informática",
        "codigo": "TIC-01",
        "descripcion": "Departamento de soporte y sistemas",
    }
    resp = client.post("/api/v1/areas", json=payload, headers=headers_admin)
    assert resp.status_code == 201
    data = resp.json()
    assert data["nombre"] == "Tecnología e Informática"
    assert data["codigo"] == "TIC-01"
    assert data["estado"] == "activo"

    # Verificar registro en auditoría
    evento = (
        db_session.query(AuditoriaSistema)
        .filter(
            AuditoriaSistema.accion == "crear_area",
            AuditoriaSistema.recurso == "area",
            AuditoriaSistema.recurso_id == data["id"],
        )
        .first()
    )
    assert evento is not None
    assert evento.resultado == "exito"


# ── Test 6: Crear área con nombre duplicado → 409 ──
def test_crear_area_nombre_duplicado_409(client, usuario_admin, area_ejemplo):
    headers_admin = get_auth_headers(usuario_admin)

    payload = {
        "nombre": area_ejemplo.nombre,
        "codigo": "OTRO-01",
    }
    resp = client.post("/api/v1/areas", json=payload, headers=headers_admin)
    assert resp.status_code == 409
    assert "Ya existe un área con ese nombre" in resp.json()["detail"]


# ── Test 7: Administrador edita área → 200 ──
def test_administrador_edita_area_200(client, db_session, usuario_admin, area_ejemplo):
    headers_admin = get_auth_headers(usuario_admin)

    payload = {
        "nombre": "Almacén Modificado",
        "descripcion": "Descripción actualizada",
    }
    resp = client.put(f"/api/v1/areas/{area_ejemplo.id}", json=payload, headers=headers_admin)
    assert resp.status_code == 200
    data = resp.json()
    assert data["nombre"] == "Almacén Modificado"
    assert data["descripcion"] == "Descripción actualizada"


# ── Test 8: Desactivar (baja lógica) y reactivar área → 200 ──
def test_desactivar_y_reactivar_area(client, db_session, usuario_admin, area_ejemplo):
    headers_admin = get_auth_headers(usuario_admin)

    # Desactivar
    resp_desact = client.patch(
        f"/api/v1/areas/{area_ejemplo.id}/desactivar",
        headers=headers_admin,
    )
    assert resp_desact.status_code == 200
    assert resp_desact.json()["estado"] == "baja"

    # Verificar que aparece en lista con filtro estado=baja
    resp_filtro = client.get("/api/v1/areas?estado=baja", headers=headers_admin)
    assert any(a["id"] == area_ejemplo.id for a in resp_filtro.json())

    # Reactivar
    resp_react = client.patch(
        f"/api/v1/areas/{area_ejemplo.id}/reactivar",
        headers=headers_admin,
    )
    assert resp_react.status_code == 200
    assert resp_react.json()["estado"] == "activo"
