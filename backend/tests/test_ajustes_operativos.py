"""Las rectificaciones conservan la operación original y crean asientos nuevos."""
from uuid import uuid4

from app.models.activos import Existencia
from app.models.auditoria import AuditoriaSistema
from app.models.inventario import AperturaInventario
from app.models.kardex import MovimientoKardex
from app.core.config import settings
from test_kardex import activos_prueba, auth_headers
from test_transferencias_area import escenario


def prueba_movimiento(client, usuario, articulo, area, *, tipo="salida", cantidad=2):
    payload = {"solicitud_id": str(uuid4()), "articulo_id": articulo.id,
               "tipo": tipo, "cantidad": cantidad, "area_operativa_id": area.id,
               "nodo_grafo": "Ventas" if tipo == "salida" else "Inventario / Compra",
               "tipo_operacion": "Ventas" if tipo == "salida" else "Inventario / Compra",
               "receptor": "Biblioteca" if tipo == "salida" else None,
               "receptor_tipo": "INSTITUCION" if tipo == "salida" else None,
               "referencia_documento": "FACT-PRUEBA-01"}
    resultado = client.post("/api/v1/kardex/movimiento-actual",
                            headers=auth_headers(usuario), json=payload)
    if resultado.status_code == 409 and isinstance(resultado.json().get("detail"), dict):
        payload["confirmacion_alertas"] = resultado.json()["detail"]["firma_confirmacion"]
        payload["motivo_alertas"] = "Operación autorizada en prueba"
        resultado = client.post("/api/v1/kardex/movimiento-actual",
                                headers=auth_headers(usuario), json=payload)
    assert resultado.status_code == 200, resultado.text
    return resultado.json()


def rectificacion(cantidad, **cambios):
    return {"solicitud_id": str(uuid4()), "cantidad_corregida": cantidad,
            "motivo": "Cantidad original revisada con documento físico",
            "referencia_documento": "ACTA-CORRECCION-01", **cambios}


def test_rectificacion_y_reversion_conservan_original_y_ajustan_stock(
    client, db_session, usuario_admin, usuario_operador, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, _ = escenario(client, db_session, usuario_admin, articulo)
    original = prueba_movimiento(client, usuario_operador, articulo, origen)
    ruta = f"/api/v1/kardex/movimiento-actual/{original['id']}/corregir"
    headers = auth_headers(usuario_admin)
    payload = rectificacion(1)
    assert client.post(ruta, headers=auth_headers(usuario_operador), json=payload).status_code == 403
    primera = client.post(ruta, headers=headers, json=payload)
    repetida = client.post(ruta, headers=headers, json=payload)
    assert primera.status_code == repetida.status_code == 200, primera.text
    assert primera.json()["id"] == repetida.json()["id"]
    assert (primera.json()["ingresos"], primera.json()["salidas"]) == (1, None)
    assert primera.json()["corrige_movimiento_id"] == original["id"]
    assert (primera.json()["cantidad_anterior"], primera.json()["cantidad_corregida"]) == (2, 1)
    assert primera.json()["autorizado_por_id"] == usuario_admin.id
    assert client.post(ruta, headers=headers, json={**payload, "cantidad_corregida": 0}).status_code == 409
    reverso = client.post(ruta, headers=headers, json=rectificacion(0))
    assert reverso.status_code == 200, reverso.text
    assert reverso.json()["saldo_registrado"] == 10
    original_db = db_session.get(MovimientoKardex, original["id"])
    assert original_db.estado == "ACTIVO"
    assert (original_db.salidas, original_db.saldo_registrado) == (2, 8)
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 10
    assert db_session.query(Existencia).filter_by(
        activo_id=articulo.id, area_id=origen.id).first().cantidad == 6
    assert client.get(f"/api/v1/kardex/devoluciones-disponibles/{articulo.id}",
                      headers=headers).json() == []
    libro = client.get(f"/api/v1/kardex/articulos/{articulo.id}/kardex-digital",
                       headers=headers).json()
    assert libro["integridad"] is True and libro["saldo_final"] == 10
    assert db_session.query(AuditoriaSistema).filter_by(
        accion="rectificar_movimiento_operativo").count() == 2
    assert client.post(f"/api/v1/kardex/movimiento-actual/{original['id']}/anular",
                       headers=headers).status_code == 410


def test_ajuste_documentado_valida_area_y_saldo(
    client, db_session, usuario_admin, usuario_operador, activos_prueba,
    monkeypatch,
):
    monkeypatch.setattr(settings, "CONTROL_CANTIDAD_EXTREMA", 2)
    articulo, _ = activos_prueba
    origen, _ = escenario(client, db_session, usuario_admin, articulo)
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/ajustes-operativos"
    payload = {"solicitud_id": str(uuid4()), "direccion": "salida", "cantidad": 2,
               "area_id": origen.id, "encargado_id": usuario_admin.id,
               "motivo": "Diferencia verificada durante recuento físico",
               "referencia_documento": "ACTA-AJUSTE-01"}
    assert client.post(ruta, headers=auth_headers(usuario_operador), json=payload).status_code == 403
    assert client.post(ruta, headers=auth_headers(usuario_admin),
                       json={**payload, "cantidad": 7}).status_code == 409
    primero = client.post(ruta, headers=auth_headers(usuario_admin), json=payload)
    repetido = client.post(ruta, headers=auth_headers(usuario_admin), json=payload)
    assert primero.status_code == repetido.status_code == 200, primero.text
    assert primero.json()["id"] == repetido.json()["id"]
    assert primero.json()["saldo_registrado"] == 8
    assert primero.json()["motivo_correccion"] == payload["motivo"]
    assert "CANTIDAD_EXTREMA" in {
        aviso["codigo"] for aviso in primero.json()["alertas_control"]}
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 8
    assert db_session.query(AuditoriaSistema).filter_by(
        accion="ajustar_inventario_operativo").count() == 1
