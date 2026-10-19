"""La devolución de una salida moderna conserva el vínculo y el límite acumulado."""
from uuid import uuid4

from app.models.activos import Existencia
from app.models.inventario import AperturaInventario
from app.models.kardex import MovimientoKardex
from test_kardex import activos_prueba, auth_headers
from test_transferencias_area import escenario
from test_ajustes_operativos import rectificacion


RUTA = "/api/v1/kardex/movimiento-actual"


def test_devoluciones_parciales_no_superan_entrega_y_admiten_reintento(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    headers = auth_headers(usuario_admin)
    venta = client.post(RUTA, headers=headers, json={
        "articulo_id": articulo.id, "solicitud_id": str(uuid4()),
        "tipo": "salida", "cantidad": 4, "tipo_operacion": "Ventas",
        "nodo_grafo": "Ventas", "encargado_id": usuario_admin.id,
        "area_operativa_id": origen.id, "receptor": "Biblioteca Municipal",
        "receptor_tipo": "INSTITUCION", "referencia_documento": "FACT-2026-001",
    })
    assert venta.status_code == 200, venta.text
    original = venta.json()["id"]
    ruta_disponibles = f"/api/v1/kardex/devoluciones-disponibles/{articulo.id}"
    assert client.get(ruta_disponibles, headers=headers).json()[0]["cantidad_pendiente"] == 4

    devolucion = {
        "articulo_id": articulo.id, "solicitud_id": str(uuid4()),
        "tipo": "ingreso", "cantidad": 2, "tipo_operacion": "Devolución",
        "nodo_grafo": "Devolución", "encargado_id": usuario_admin.id,
        "area_operativa_id": destino.id, "movimiento_origen_id": original,
        "devuelto_por": "Biblioteca Municipal", "referencia_documento": "ACTA-DEV-01",
    }
    primera = client.post(RUTA, headers=headers, json=devolucion)
    repetida = client.post(RUTA, headers=headers, json=devolucion)
    assert primera.status_code == repetida.status_code == 200, primera.text
    assert primera.json()["id"] == repetida.json()["id"]
    assert primera.json()["movimiento_origen_id"] == original
    assert primera.json()["devuelto_por"] == "Biblioteca Municipal"
    assert primera.json()["saldo_registrado"] == 8
    assert client.get(ruta_disponibles, headers=headers).json()[0]["cantidad_pendiente"] == 2
    assert client.post(RUTA, headers=headers, json={**devolucion,
        "cantidad": 3, "solicitud_id": str(uuid4())}).status_code == 409
    assert client.post(RUTA, headers=headers, json={**devolucion,
        "cantidad": 1}).status_code == 409
    assert client.post(f"{RUTA}/{original}/anular", headers=headers).status_code == 410
    assert client.post(f"{RUTA}/{original}/corregir", headers=headers,
                       json=rectificacion(1)).status_code == 409
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 8
    assert {e.area_id: e.cantidad for e in db_session.query(Existencia).filter_by(
        activo_id=articulo.id).all()} == {origen.id: 2, destino.id: 6}

    ultima = client.post(RUTA, headers=headers, json={**devolucion,
        "solicitud_id": str(uuid4()), "referencia_documento": "ACTA-DEV-02"})
    assert ultima.status_code == 200, ultima.text
    assert client.get(ruta_disponibles, headers=headers).json() == []
    libro = client.get(f"/api/v1/kardex/articulos/{articulo.id}/kardex-digital",
                       headers=headers).json()
    assert libro["saldo_final"] == 10 and libro["integridad"] is True
    assert [e["movimiento_origen_id"] for e in libro["eventos"]
            if e["descripcion"] == "Devolución"] == [original, original]
    csv = client.get(f"/api/v1/kardex/articulos/{articulo.id}/kardex-digital.csv",
                     headers=headers)
    assert csv.status_code == 200
    assert "entrega_original_id" in csv.text
    assert "Biblioteca Municipal" in csv.text
    assert db_session.query(MovimientoKardex).filter_by(
        movimiento_origen_id=original, estado="ACTIVO").count() == 2
    assert client.post(f"{RUTA}/{ultima.json()['id']}/corregir", headers=headers,
                       json=rectificacion(0)).status_code == 200
    assert client.get(ruta_disponibles, headers=headers).json()[0]["cantidad_pendiente"] == 2
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 8


def test_devolucion_exige_entrega_valida_y_recepcion_identificada(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, _ = escenario(client, db_session, usuario_admin, articulo)
    headers = auth_headers(usuario_admin)
    payload = {
        "articulo_id": articulo.id, "solicitud_id": str(uuid4()),
        "tipo": "ingreso", "cantidad": 1, "tipo_operacion": "Devolución",
        "nodo_grafo": "Devolución", "encargado_id": usuario_admin.id,
        "area_operativa_id": origen.id, "devuelto_por": "Cliente",
        "referencia_documento": "ACTA-DEV-01",
    }
    assert client.post(RUTA, headers=headers, json=payload).status_code == 409
    assert client.post(RUTA, headers=headers, json={**payload,
        "movimiento_origen_id": 9999}).status_code == 409
    assert client.post(RUTA, headers=headers, json={**payload,
        "movimiento_origen_id": 9999, "devuelto_por": " "}).status_code == 422
    assert client.post(RUTA, headers=headers, json={**payload,
        "movimiento_origen_id": 9999, "area_operativa_id": None}).status_code == 422
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 10
    assert db_session.query(MovimientoKardex).count() == 0
