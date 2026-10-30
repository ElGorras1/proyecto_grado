import pytest
from datetime import date
from sqlalchemy import text
from app.models.area import Area
from app.models.catalogo_areas import CatalogoArea, SinonimoArea
from app.models.auditoria import AuditoriaSistema
from app.models.activos import Existencia
from app.services.clasificador_nodos import clasificar_movimiento, AREA_PENDIENTE_HIL, AREA_RESUELTA_AUTOMATICAMENTE
from test_kardex import activos_prueba, auth_headers, crear_movimiento, usuario_auditor

RAIZ = "/api/v1/administracion/areas"
MOTIVO = "Revisión administrativa con referencia de prueba QA 01."


def nueva_area(client, usuario, **campos):
    return client.post(RAIZ, headers=auth_headers(usuario),
                       json={"nombre": "Deposito", "codigo": "DEP", "motivo": MOTIVO, **campos})


def actualizar(client, usuario, ruta, anterior, **campos):
    datos = {k: v for k, v in anterior.items() if k not in ("id", "dependencias")}
    return client.put(ruta + "/" + str(anterior["id"]), headers=auth_headers(usuario),
                      json={**datos, "motivo": MOTIVO, **campos})


def test_area_alta_edicion_baja_reactivacion_y_auditoria(client, db_session, usuario_admin):
    r = nueva_area(client, usuario_admin)
    assert r.status_code == 201
    anterior = r.json()
    r = actualizar(client, usuario_admin, RAIZ, anterior, descripcion="Almacén confirmado", estado="baja")
    assert r.status_code == 200
    assert db_session.get(Area, anterior["id"]).estado == "baja"
    assert actualizar(client, usuario_admin, RAIZ, r.json(), estado="activo").status_code == 200
    assert actualizar(client, usuario_admin, RAIZ, anterior, estado="baja").status_code == 409
    cambios = db_session.query(AuditoriaSistema).filter_by(accion="administrar_areas_catalogos").all()
    assert len(cambios) == 3 and cambios[1].detalle["previo"]["estado"] == "activo"
    assert all(c.detalle["motivo"] == MOTIVO for c in cambios)
    consulta = client.get(RAIZ + "/historial", headers=auth_headers(usuario_admin),
                          params=dict(recurso="area", registro_id=anterior["id"]))
    assert consulta.status_code == 200 and len(consulta.json()) == 3
    assert consulta.json()[0]["usuario"] == usuario_admin.nombre


@pytest.mark.parametrize("campos", [{"nombre": " deposito "}, {"nombre": "Otro", "codigo": " dep "}])
def test_unicidad_normalizada_incluye_bajas(client, usuario_admin, campos):
    assert nueva_area(client, usuario_admin, estado="baja").status_code == 201
    assert nueva_area(client, usuario_admin, **campos).status_code == 409


@pytest.mark.parametrize("nombre", ["", "    ", "x" * 121])
def test_nombres_invalidos(client, usuario_admin, nombre):
    assert nueva_area(client, usuario_admin, nombre=nombre).status_code == 422


@pytest.mark.parametrize("tipo", ["stock", "usuario"])
def test_baja_protegida_y_nombre_usado_estable(client, db_session, usuario_admin, activos_prueba, tipo):
    a = nueva_area(client, usuario_admin).json()
    if tipo == "stock":
        db_session.add(Existencia(activo_id=activos_prueba[0].id, area_id=a["id"], cantidad=3))
    else:
        usuario_admin.area_id = a["id"]
    db_session.commit()
    assert actualizar(client, usuario_admin, RAIZ, a, estado="baja").status_code == 409
    assert actualizar(client, usuario_admin, RAIZ, a, nombre="Otra identidad").status_code == 409
    assert db_session.get(Area, a["id"]).estado == "activo"


@pytest.mark.parametrize("ruta", ["", "/catalogo/historico", "/catalogo/alias", "/personas/adscripciones"])
def test_roles_lectura_y_api_directa(client, usuario_admin, usuario_auditor, usuario_operador, ruta):
    assert client.get(RAIZ + ruta).status_code == 401
    assert client.get(RAIZ + ruta, headers=auth_headers(usuario_operador)).status_code == 403
    assert client.get(RAIZ + ruta, headers=auth_headers(usuario_auditor)).status_code == 200
    for usuario in (usuario_auditor, usuario_operador):
        assert client.post(RAIZ + ruta, headers=auth_headers(usuario), json={}).status_code in (403, 405)
        assert client.put(RAIZ + ruta + "/1", headers=auth_headers(usuario), json={}).status_code == 403


def test_catalogo_historico_no_crea_ubicacion_y_conserva_identidad(client, db_session, usuario_admin):
    h = auth_headers(usuario_admin)
    r = client.post(RAIZ + "/catalogo/historico", headers=h,
                    json=dict(nombre_oficial="C+C", abreviatura="C+C", activa=False, motivo=MOTIVO))
    assert r.status_code == 201
    cat = r.json()
    assert db_session.query(Area).count() == 0
    nodos = client.get("/api/v1/kardex/nodos", headers=h).json()
    assert any(n["valor"] == "Área: C+C" and "histórica" in n["etiqueta"] for n in nodos)
    alias = client.post(RAIZ + "/catalogo/alias", headers=h,
                       json=dict(texto_sucio="CTC", area_oficial_id=cat["id"], motivo=MOTIVO))
    assert alias.status_code == 201
    assert actualizar(client, usuario_admin, RAIZ + "/catalogo/historico", cat,
                      nombre_oficial="Unidad moderna").status_code == 409
    assert actualizar(client, usuario_admin, RAIZ + "/catalogo/historico", cat,
                      descripcion="Área antigua cerrada; se conserva el archivo").status_code == 200


def test_alias_confirmacion_baja_y_historico_no_reescrito(client, db_session, usuario_admin, activos_prueba):
    cat = CatalogoArea(nombre_oficial="Sala", abreviatura="SALA", tipo="departamento", activa=True)
    db_session.add(cat); db_session.commit()
    historico = crear_movimiento(db_session, articulo_id=activos_prueba[0].id,
        fecha=date(2024, 1, 1), saldo=1, ingresos=1)
    historico.area = "SALLA"
    historico.nodo_grafo = "Área no catalogada"
    historico.area_estado = "PENDIENTE_HIL"
    db_session.commit()
    h = auth_headers(usuario_admin)
    r = client.post(RAIZ + "/catalogo/alias", headers=h,
        json=dict(texto_sucio="SALLA", area_oficial_id=cat.id, motivo=MOTIVO))
    assert r.status_code == 201
    alias = r.json()
    assert clasificar_movimiento("Traslado", None, "SALLA", 1, 0, db_session).area_estado == AREA_PENDIENTE_HIL
    assert actualizar(client, usuario_admin, RAIZ + "/catalogo/alias", alias, confirmado=True).status_code == 422
    confirmado = actualizar(client, usuario_admin, RAIZ + "/catalogo/alias", alias, confirmado=True, evidencia_revisada=True)
    assert confirmado.status_code == 200
    assert clasificar_movimiento("Traslado", None, "SALLA", 1, 0, db_session).area_estado == AREA_RESUELTA_AUTOMATICAMENTE
    baja = actualizar(client, usuario_admin, RAIZ + "/catalogo/alias", confirmado.json(), activa=False, evidencia_revisada=True)
    assert baja.status_code == 200
    assert clasificar_movimiento("Traslado", None, "SALLA", 1, 0, db_session).area_estado == AREA_PENDIENTE_HIL
    db_session.refresh(historico)
    assert historico.area == "SALLA" and historico.nodo_grafo == "Área no catalogada" and historico.area_estado == "PENDIENTE_HIL"


def test_alias_no_suplanta_nombre_o_sigla(client, db_session, usuario_admin):
    a = CatalogoArea(nombre_oficial="Galeria", abreviatura="GAL")
    b = CatalogoArea(nombre_oficial="Sala", abreviatura="SALA")
    db_session.add_all([a, b]); db_session.commit()
    r = client.post(RAIZ + "/catalogo/alias", headers=auth_headers(usuario_admin),
        json=dict(texto_sucio="GAL", area_oficial_id=b.id, confirmado=True, evidencia_revisada=True, motivo=MOTIVO))
    assert r.status_code == 409
    assert db_session.query(SinonimoArea).count() == 0


def test_adscripcion_no_cambia_rol_y_protege_baja(client, db_session, usuario_admin, usuario_operador):
    a = nueva_area(client, usuario_admin).json()
    h = auth_headers(usuario_admin)
    lista = client.get(RAIZ + "/personas/adscripciones", headers=h).json()
    persona = next(p for p in lista if p["id"] == usuario_operador.id)
    payload = dict(area_id=a["id"], version=persona["version"], motivo=MOTIVO)
    ruta = RAIZ + "/personas/adscripciones/" + str(persona["id"])
    r = client.put(ruta, headers=h, json=payload)
    assert r.status_code == 200
    assert usuario_operador.area_id == a["id"] and usuario_operador.rol.nombre == "Operador"
    assert actualizar(client, usuario_admin, RAIZ, a, estado="baja").status_code == 409
    r = client.put(ruta, headers=h, json=dict(area_id=None, version=r.json()["version"], motivo=MOTIVO))
    assert r.status_code == 200
    assert actualizar(client, usuario_admin, RAIZ, a, estado="baja").status_code == 200
    assert client.put(ruta, headers=h, json=dict(area_id=a["id"], version=r.json()["version"], motivo=MOTIVO)).status_code == 422


def test_historial_exige_permiso_y_conserva_datos_limitados(client, usuario_admin, usuario_auditor, usuario_operador):
    area = nueva_area(client, usuario_admin).json()
    params = dict(recurso="area", registro_id=area["id"])
    assert client.get(RAIZ + "/historial", params=params).status_code == 401
    assert client.get(RAIZ + "/historial", params=params, headers=auth_headers(usuario_operador)).status_code == 403
    r = client.get(RAIZ + "/historial", params=params, headers=auth_headers(usuario_auditor))
    assert r.status_code == 200 and r.json()[0]["detalle"]["motivo"] == MOTIVO
    assert "password" not in r.text and "email" not in r.text


def test_api_usuarios_no_asigna_bajas_ni_reactiva_adscripcion_inactiva(client, db_session, usuario_admin, usuario_operador):
    a = nueva_area(client, usuario_admin, estado="baja").json()
    h = auth_headers(usuario_admin)
    assert client.put(f"/api/v1/usuarios/{usuario_operador.id}", headers=h,
                      json=dict(area_id=a["id"])).status_code == 400
    usuario_operador.area_id = a["id"]
    usuario_operador.estado = "baja"
    db_session.commit()
    assert client.patch(f"/api/v1/usuarios/{usuario_operador.id}/reactivar", headers=h).status_code == 409
    assert client.put(f"/api/v1/usuarios/{usuario_operador.id}", headers=h, json=dict(area_id=None)).status_code == 200
    assert client.patch(f"/api/v1/usuarios/{usuario_operador.id}/reactivar", headers=h).status_code == 200
