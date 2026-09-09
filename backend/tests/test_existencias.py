import pytest
from app.core.security import create_access_token
from app.models.activos import Activo, CategoriaActivo, Existencia
from app.models.area import Area
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
    cat = CategoriaActivo(nombre="Mobiliario y Equipos", codigo="CAT-MOB-01", estado="activo")
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def area(db_session):
    ar = Area(nombre="Almacén Secundario", codigo="ALM-02", estado="activo")
    db_session.add(ar)
    db_session.commit()
    db_session.refresh(ar)
    return ar


@pytest.fixture
def activo(db_session, categoria):
    act = Activo(
        categoria_id=categoria.id,
        codigo="ACT-EXT-01",
        nombre="Silla Ergonómica Pro",
        unidad_medida="unidad",
        estado="activo",
    )
    db_session.add(act)
    db_session.commit()
    db_session.refresh(act)
    return act


@pytest.fixture
def existencia_ejemplo(db_session, activo, area):
    ex = Existencia(
        activo_id=activo.id,
        area_id=area.id,
        cantidad=15,
        stock_minimo=5,
        stock_maximo=50,
        estado="activo",
    )
    db_session.add(ex)
    db_session.commit()
    db_session.refresh(ex)
    return ex


# ── Test 1: GET sin token → 401 ──
def test_listar_existencias_sin_token_401(client):
    resp = client.get("/api/v1/existencias")
    assert resp.status_code == 401


# ── Test 2: GET abierto a Administrador, Operador y Auditor → 200 ──
def test_listar_existencias_tres_roles_200(client, usuario_admin, usuario_operador, usuario_auditor, existencia_ejemplo):
    for usuario in [usuario_admin, usuario_operador, usuario_auditor]:
        resp = client.get("/api/v1/existencias", headers=get_auth_headers(usuario))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["activo_nombre"] == "Silla Ergonómica Pro"
        assert data[0]["area_nombre"] == "Almacén Secundario"


# ── Test 3: GET detalle por ID (200 y 404) ──
def test_obtener_existencia_detalle(client, usuario_auditor, existencia_ejemplo):
    resp = client.get(f"/api/v1/existencias/{existencia_ejemplo.id}", headers=get_auth_headers(usuario_auditor))
    assert resp.status_code == 200
    data = resp.json()
    assert data["cantidad"] == 15.0
    assert data["activo_nombre"] == "Silla Ergonómica Pro"
    assert data["area_nombre"] == "Almacén Secundario"

    resp_404 = client.get("/api/v1/existencias/99999", headers=get_auth_headers(usuario_auditor))
    assert resp_404.status_code == 404


# ── Test 4: RBAC POST — Admin y Operador (201), Auditor → 403 ──
def test_rbac_crear_existencia(client, db_session, usuario_admin, usuario_operador, usuario_auditor, categoria):
    # Crear un activo y área nuevos
    area_nueva = Area(nombre="Oficina Principal", codigo="OFI-01", estado="activo")
    activo_nuevo = Activo(
        categoria_id=categoria.id,
        codigo="ACT-NEW-EX",
        nombre="Escritorio Ejecutivo",
        estado="activo",
    )
    db_session.add_all([area_nueva, activo_nuevo])
    db_session.commit()

    payload = {
        "activo_id": activo_nuevo.id,
        "area_id": area_nueva.id,
        "cantidad": 20,
        "stock_minimo": 2,
        "stock_maximo": 30,
    }

    # Auditor -> 403
    resp_aud = client.post("/api/v1/existencias", json=payload, headers=get_auth_headers(usuario_auditor))
    assert resp_aud.status_code == 403

    # Operador -> 201
    resp_op = client.post("/api/v1/existencias", json=payload, headers=get_auth_headers(usuario_operador))
    assert resp_op.status_code == 201
    data_op = resp_op.json()
    assert data_op["cantidad"] == 20.0
    assert data_op["activo_nombre"] == "Escritorio Ejecutivo"
    assert data_op["area_nombre"] == "Oficina Principal"

    # Verificar auditoría
    evento = (
        db_session.query(AuditoriaSistema)
        .filter(
            AuditoriaSistema.accion == "crear_existencia",
            AuditoriaSistema.recurso == "existencia",
            AuditoriaSistema.recurso_id == data_op["id"],
        )
        .first()
    )
    assert evento is not None
    assert evento.resultado == "exito"


# ── Test 5: Validaciones de FKs y unicidad (activo_id, area_id) → 400 y 409 ──
def test_crear_existencia_validaciones(client, usuario_operador, activo, area, existencia_ejemplo):
    # Activo inexistente -> 400
    resp_act_inex = client.post(
        "/api/v1/existencias",
        json={"activo_id": 9999, "area_id": area.id, "cantidad": 5},
        headers=get_auth_headers(usuario_operador),
    )
    assert resp_act_inex.status_code == 400

    # Área inexistente -> 400
    resp_area_inex = client.post(
        "/api/v1/existencias",
        json={"activo_id": activo.id, "area_id": 9999, "cantidad": 5},
        headers=get_auth_headers(usuario_operador),
    )
    assert resp_area_inex.status_code == 400

    # Par (activo_id, area_id) duplicado -> 409
    resp_dup = client.post(
        "/api/v1/existencias",
        json={"activo_id": activo.id, "area_id": area.id, "cantidad": 10},
        headers=get_auth_headers(usuario_operador),
    )
    assert resp_dup.status_code == 409
    assert "Ya existe un registro de existencia" in resp_dup.json()["detail"]


# ── Test 6: RBAC PUT — Operador edita cantidad y stock_min/max (200), Auditor → 403 ──
def test_rbac_actualizar_existencia(client, usuario_operador, usuario_auditor, existencia_ejemplo):
    payload = {"cantidad": 25, "stock_minimo": 8, "stock_maximo": 60}

    # Auditor -> 403
    resp_aud = client.put(f"/api/v1/existencias/{existencia_ejemplo.id}", json=payload, headers=get_auth_headers(usuario_auditor))
    assert resp_aud.status_code == 403

    # Operador -> 200
    resp_op = client.put(f"/api/v1/existencias/{existencia_ejemplo.id}", json=payload, headers=get_auth_headers(usuario_operador))
    assert resp_op.status_code == 200
    data = resp_op.json()
    assert data["cantidad"] == 25.0
    assert data["stock_minimo"] == 8.0
    assert data["stock_maximo"] == 60.0

    # Validación: stock_maximo < stock_minimo -> 400
    resp_invalido = client.put(
        f"/api/v1/existencias/{existencia_ejemplo.id}",
        json={"stock_minimo": 50, "stock_maximo": 10},
        headers=get_auth_headers(usuario_operador),
    )
    assert resp_invalido.status_code == 400 or resp_invalido.status_code == 422


# ── Test 7: RBAC Desactivar y Reactivar existencia (baja lógica) ──
def test_rbac_desactivar_y_reactivar_existencia(client, usuario_operador, usuario_auditor, existencia_ejemplo):
    # Auditor -> 403
    resp_aud = client.patch(f"/api/v1/existencias/{existencia_ejemplo.id}/desactivar", headers=get_auth_headers(usuario_auditor))
    assert resp_aud.status_code == 403

    # Operador desactiva -> 200 (estado = 'baja')
    resp_des = client.patch(f"/api/v1/existencias/{existencia_ejemplo.id}/desactivar", headers=get_auth_headers(usuario_operador))
    assert resp_des.status_code == 200
    assert resp_des.json()["estado"] == "baja"

    # Operador reactiva -> 200 (estado = 'activo')
    resp_rea = client.patch(f"/api/v1/existencias/{existencia_ejemplo.id}/reactivar", headers=get_auth_headers(usuario_operador))
    assert resp_rea.status_code == 200
    assert resp_rea.json()["estado"] == "activo"
