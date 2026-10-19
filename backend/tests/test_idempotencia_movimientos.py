"""Una solicitud repetida no debe volver a modificar el inventario."""
from uuid import uuid4

from app.models.auditoria import AuditoriaSistema
from app.models.inventario import AperturaInventario
from app.models.kardex import MovimientoKardex
from test_kardex import activos_prueba, auth_headers


def test_reintento_devuelve_el_mismo_asiento_y_reutilizar_clave_distinta_falla(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    headers = auth_headers(usuario_admin)
    apertura = client.post(f"/api/v1/kardex/articulos/{articulo.id}/apertura",
        headers=headers, json={"cantidad": 10, "referencia_documento": "ACTA-01",
                               "justificacion": "Conteo físico verificado",
                               "conteo_verificado": True})
    assert apertura.status_code == 200
    solicitud = str(uuid4())
    datos = {"solicitud_id": solicitud, "articulo_id": articulo.id,
             "tipo": "ingreso", "cantidad": 2,
             "nodo_grafo": "Inventario / Compra",
             "tipo_operacion": "Inventario / Compra",
             "referencia_documento": "FACT-01"}

    primero = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
        json=datos)
    repetido = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
        json=datos)
    cambiado = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
        json={**datos, "cantidad": 3})

    assert primero.status_code == repetido.status_code == 200
    assert primero.json()["id"] == repetido.json()["id"]
    assert repetido.json()["solicitud_id"] == solicitud
    assert cambiado.status_code == 409
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 12
    assert db_session.query(MovimientoKardex).count() == 1
    assert db_session.query(AuditoriaSistema).filter_by(
        accion="crear_movimiento_inventario").count() == 1


def test_clave_obligatoria_y_unica_entre_articulos(
    client, db_session, usuario_admin, activos_prueba,
):
    primero, segundo = activos_prueba
    headers = auth_headers(usuario_admin)
    for articulo in (primero, segundo):
        assert client.post(f"/api/v1/kardex/articulos/{articulo.id}/apertura",
            headers=headers, json={"cantidad": 0, "referencia_documento": "ACTA-01",
                                   "justificacion": "Conteo físico verificado",
                                   "conteo_verificado": True}).status_code == 200
    solicitud = str(uuid4())
    base = {"solicitud_id": solicitud, "tipo": "ingreso", "cantidad": 1,
            "nodo_grafo": "Inventario / Compra",
            "referencia_documento": "FACT-01"}
    sin_clave = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
        json={"articulo_id": primero.id, **{k: v for k, v in base.items()
                                              if k != "solicitud_id"}})
    registrado = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
        json={"articulo_id": primero.id, **base})
    colision = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
        json={"articulo_id": segundo.id, **base})

    assert sin_clave.status_code == 422
    assert registrado.status_code == 200
    assert colision.status_code == 409
    assert db_session.get(AperturaInventario, primero.id).cantidad_actual == 1
    assert db_session.get(AperturaInventario, segundo.id).cantidad_actual == 0
    assert db_session.query(MovimientoKardex).count() == 1
