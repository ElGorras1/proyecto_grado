import pytest
from app.core.security import create_access_token
from app.models.activos import Activo, CategoriaActivo
from app.models.auditoria import AuditoriaSistema
from app.models.usuario import Usuario


def get_auth_headers(usuario: Usuario) -> dict[str, str]:
    token = create_access_token(
        subject=usuario.id,
        extra_claims={"rol": usuario.rol.nombre},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def categoria(db_session):
    cat = CategoriaActivo(
        nombre="Laptops y Computadoras",
        codigo="CAT-LAP",
        descripcion="Equipos portátiles",
        estado="activo",
    )
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def activo_ejemplo(db_session, categoria):
    act = Activo(
        categoria_id=categoria.id,
        codigo="ACT-001",
        nombre="ThinkPad T14",
        descripcion="Laptop Lenovo ThinkPad",
        unidad_medida="unidad",
        estado="activo",
    )
    db_session.add(act)
    db_session.commit()
    db_session.refresh(act)
    return act


# ── Test 1: GET sin token → 401 ──
def test_listar_activos_sin_token_401(client):
    resp = client.get("/api/v1/activos")
    assert resp.status_code == 401


# ── Test 2: GET abierto a Administrador, Operador y Auditor → 200 ──
def test_listar_activos_tres_roles_200(client, usuario_admin, usuario_operador, usuario_auditor, activo_ejemplo):
    for usuario in [usuario_admin, usuario_operador, usuario_auditor]:
        resp = client.get("/api/v1/activos", headers=get_auth_headers(usuario))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert any(a["codigo"] == "ACT-001" for a in data)


# ── Test 3: GET detalle por ID (200 y 404), con categoria_nombre legible ──
def test_obtener_activo_detalle(client, usuario_auditor, activo_ejemplo):
    resp = client.get(f"/api/v1/activos/{activo_ejemplo.id}", headers=get_auth_headers(usuario_auditor))
    assert resp.status_code == 200
    data = resp.json()
    assert data["codigo"] == "ACT-001"
    assert data["categoria_nombre"] == "Laptops y Computadoras"

    resp_404 = client.get("/api/v1/activos/99999", headers=get_auth_headers(usuario_auditor))
    assert resp_404.status_code == 404


# ── Test 4: RBAC POST — Admin y Operador (201), Auditor → 403 ──
def test_rbac_crear_activo(client, db_session, usuario_admin, usuario_operador, usuario_auditor, categoria):
    payload = {
        "categoria_id": categoria.id,
        "codigo": "ACT-OP-01",
        "nombre": "Dell Latitude 5420",
        "unidad_medida": "unidad",
    }

    # Auditor -> 403
    resp_aud = client.post("/api/v1/activos", json=payload, headers=get_auth_headers(usuario_auditor))
    assert resp_aud.status_code == 403

    # Operador -> 201
    resp_op = client.post("/api/v1/activos", json=payload, headers=get_auth_headers(usuario_operador))
    assert resp_op.status_code == 201
    data_op = resp_op.json()
    assert data_op["codigo"] == "ACT-OP-01"
    assert data_op["categoria_nombre"] == "Laptops y Computadoras"

    # Administrador -> 201
    payload_admin = {
        "categoria_id": categoria.id,
        "codigo": "ACT-ADM-01",
        "nombre": "MacBook Pro M2",
        "unidad_medida": "unidad",
    }
    resp_adm = client.post("/api/v1/activos", json=payload_admin, headers=get_auth_headers(usuario_admin))
    assert resp_adm.status_code == 201

    # Verificar auditoría
    evento = (
        db_session.query(AuditoriaSistema)
        .filter(
            AuditoriaSistema.accion == "crear_activo",
            AuditoriaSistema.recurso == "activo",
            AuditoriaSistema.recurso_id == data_op["id"],
        )
        .first()
    )
    assert evento is not None
    assert evento.resultado == "exito"


# ── Test 5: Validación de duplicados y categoría inválida ──
def test_crear_activo_validaciones(client, usuario_operador, categoria, activo_ejemplo):
    # Código duplicado -> 409
    resp_dup = client.post(
        "/api/v1/activos",
        json={
            "categoria_id": categoria.id,
            "codigo": activo_ejemplo.codigo,
            "nombre": "Otro Activo",
        },
        headers=get_auth_headers(usuario_operador),
    )
    assert resp_dup.status_code == 409

    # Categoría inexistente -> 400
    resp_cat_invalida = client.post(
        "/api/v1/activos",
        json={
            "categoria_id": 9999,
            "codigo": "ACT-NEW-99",
            "nombre": "Activo sin categoría",
        },
        headers=get_auth_headers(usuario_operador),
    )
    assert resp_cat_invalida.status_code == 400


# ── Test 6: RBAC PUT — Operador y Admin pueden editar (200), Auditor → 403 ──
def test_rbac_actualizar_activo(client, usuario_admin, usuario_operador, usuario_auditor, activo_ejemplo):
    payload = {"nombre": "ThinkPad T14 Gen 2"}

    # Auditor -> 403
    resp_aud = client.put(f"/api/v1/activos/{activo_ejemplo.id}", json=payload, headers=get_auth_headers(usuario_auditor))
    assert resp_aud.status_code == 403

    # Operador -> 200
    resp_op = client.put(f"/api/v1/activos/{activo_ejemplo.id}", json=payload, headers=get_auth_headers(usuario_operador))
    assert resp_op.status_code == 200
    assert resp_op.json()["nombre"] == "ThinkPad T14 Gen 2"


# ── Test 7: RBAC Desactivar y Reactivar (baja lógica) ──
def test_rbac_desactivar_y_reactivar_activo(client, usuario_operador, usuario_auditor, activo_ejemplo):
    # Auditor -> 403
    resp_aud = client.patch(f"/api/v1/activos/{activo_ejemplo.id}/desactivar", headers=get_auth_headers(usuario_auditor))
    assert resp_aud.status_code == 403

    # Operador desactiva -> 200 (estado = 'baja')
    resp_op_des = client.patch(f"/api/v1/activos/{activo_ejemplo.id}/desactivar", headers=get_auth_headers(usuario_operador))
    assert resp_op_des.status_code == 200
    assert resp_op_des.json()["estado"] == "baja"

    # Operador reactiva -> 200 (estado = 'activo')
    resp_op_rea = client.patch(f"/api/v1/activos/{activo_ejemplo.id}/reactivar", headers=get_auth_headers(usuario_operador))
    assert resp_op_rea.status_code == 200
    assert resp_op_rea.json()["estado"] == "activo"
