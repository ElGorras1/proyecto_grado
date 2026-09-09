import pytest
from app.core.security import create_access_token
from app.models.activos import Activo, CategoriaActivo, Existencia
from app.models.area import Area
from app.models.usuario import Usuario


def get_auth_headers(usuario: Usuario) -> dict[str, str]:
    token = create_access_token(
        subject=usuario.id,
        extra_claims={"rol": usuario.rol.nombre},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def datos_inventario(db_session):
    cat_it = CategoriaActivo(nombre="Tecnología", codigo="CAT-IT", estado="activo")
    cat_mob = CategoriaActivo(nombre="Mobiliario", codigo="CAT-MOB", estado="activo")
    db_session.add_all([cat_it, cat_mob])
    db_session.commit()

    area_1 = Area(nombre="Almacén Central", codigo="ALM-01", estado="activo")
    area_2 = Area(nombre="Sucursal Norte", codigo="SUC-01", estado="activo")
    db_session.add_all([area_1, area_2])
    db_session.commit()

    # Activo 1: Laptop con stock bajo (cantidad 2 < stock_minimo 5)
    activo_laptop = Activo(
        categoria_id=cat_it.id,
        codigo="ACT-LAP-01",
        nombre="Laptop Dell XPS",
        unidad_medida="unidad",
        estado="activo",
    )
    # Activo 2: Monitor con stock suficiente (cantidad 10 >= stock_minimo 3)
    activo_monitor = Activo(
        categoria_id=cat_it.id,
        codigo="ACT-MON-01",
        nombre="Monitor Dell 27",
        unidad_medida="unidad",
        estado="activo",
    )
    # Activo 3: Silla sin stock_minimo configurado
    activo_silla = Activo(
        categoria_id=cat_mob.id,
        codigo="ACT-SIL-01",
        nombre="Silla Giratoria",
        unidad_medida="unidad",
        estado="activo",
    )
    db_session.add_all([activo_laptop, activo_monitor, activo_silla])
    db_session.commit()

    ex1 = Existencia(
        activo_id=activo_laptop.id,
        area_id=area_1.id,
        cantidad=2,
        stock_minimo=5,
        stock_maximo=20,
        estado="activo",
    )
    ex2 = Existencia(
        activo_id=activo_monitor.id,
        area_id=area_1.id,
        cantidad=10,
        stock_minimo=3,
        stock_maximo=15,
        estado="activo",
    )
    ex3 = Existencia(
        activo_id=activo_silla.id,
        area_id=area_2.id,
        cantidad=8,
        stock_minimo=None,
        stock_maximo=None,
        estado="activo",
    )
    db_session.add_all([ex1, ex2, ex3])
    db_session.commit()

    return {
        "cat_it": cat_it,
        "cat_mob": cat_mob,
        "area_1": area_1,
        "area_2": area_2,
        "activo_laptop": activo_laptop,
        "activo_monitor": activo_monitor,
        "activo_silla": activo_silla,
        "ex1": ex1,
        "ex2": ex2,
        "ex3": ex3,
    }


# ── Test 1: GET sin token → 401 ──
def test_reporte_inventario_sin_token_401(client):
    resp = client.get("/api/v1/inventario/reporte")
    assert resp.status_code == 401


# ── Test 2: Accesible por los 3 roles (Admin, Operador, Auditor) → 200 ──
def test_reporte_inventario_tres_roles_200(client, usuario_admin, usuario_operador, usuario_auditor, datos_inventario):
    for usuario in [usuario_admin, usuario_operador, usuario_auditor]:
        resp = client.get("/api/v1/inventario/reporte", headers=get_auth_headers(usuario))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 3


# ── Test 3: Marca correctamente stock_bajo: true y false ──
def test_reporte_inventario_stock_bajo(client, usuario_auditor, datos_inventario):
    resp = client.get("/api/v1/inventario/reporte", headers=get_auth_headers(usuario_auditor))
    assert resp.status_code == 200
    data = resp.json()

    # Laptop (cantidad 2 < min 5) -> stock_bajo = True
    item_laptop = next(i for i in data if i["activo_codigo"] == "ACT-LAP-01")
    assert item_laptop["stock_bajo"] is True
    assert item_laptop["categoria_nombre"] == "Tecnología"
    assert item_laptop["area_nombre"] == "Almacén Central"

    # Monitor (cantidad 10 >= min 3) -> stock_bajo = False
    item_monitor = next(i for i in data if i["activo_codigo"] == "ACT-MON-01")
    assert item_monitor["stock_bajo"] is False

    # Silla (stock_minimo is None) -> stock_bajo = False
    item_silla = next(i for i in data if i["activo_codigo"] == "ACT-SIL-01")
    assert item_silla["stock_bajo"] is False


# ── Test 4: Filtro solo_stock_bajo = true ──
def test_reporte_inventario_filtro_solo_stock_bajo(client, usuario_operador, datos_inventario):
    resp = client.get("/api/v1/inventario/reporte?solo_stock_bajo=true", headers=get_auth_headers(usuario_operador))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["activo_codigo"] == "ACT-LAP-01"
    assert data[0]["stock_bajo"] is True


# ── Test 5: Filtro por categoria_id y area_id ──
def test_reporte_inventario_filtros_categoria_y_area(client, usuario_admin, datos_inventario):
    # Filtrar por Mobiliario
    cat_mob_id = datos_inventario["cat_mob"].id
    resp_cat = client.get(f"/api/v1/inventario/reporte?categoria_id={cat_mob_id}", headers=get_auth_headers(usuario_admin))
    assert resp_cat.status_code == 200
    data_cat = resp_cat.json()
    assert len(data_cat) == 1
    assert data_cat[0]["activo_codigo"] == "ACT-SIL-01"

    # Filtrar por Sucursal Norte (area_2)
    area_2_id = datos_inventario["area_2"].id
    resp_area = client.get(f"/api/v1/inventario/reporte?area_id={area_2_id}", headers=get_auth_headers(usuario_admin))
    assert resp_area.status_code == 200
    data_area = resp_area.json()
    assert len(data_area) == 1
    assert data_area[0]["area_nombre"] == "Sucursal Norte"
