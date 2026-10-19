"""Un traslado mueve custodia física sin restar patrimonio institucional."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import event

from app.models.activos import Existencia
from app.models.area import Area
from app.models.auditoria import AuditoriaSistema
from app.models.inventario import AperturaInventario, TransferenciaArea
from app.models.kardex import MovimientoKardex
from test_kardex import activos_prueba, auth_headers


def escenario(client, db_session, usuario_admin, articulo):
    origen = Area(nombre="Galería de prueba", estado="activo")
    destino = Area(nombre="Depósito de prueba", estado="activo")
    db_session.add_all([origen, destino])
    db_session.commit()
    headers = auth_headers(usuario_admin)
    assert client.post(f"/api/v1/kardex/articulos/{articulo.id}/apertura",
        headers=headers, json={"cantidad": 10, "referencia_documento": "ACTA-01",
                               "justificacion": "Conteo físico verificado",
                               "conteo_verificado": True}).status_code == 200
    for area, cantidad in ((origen, 6), (destino, 4)):
        assert client.post(f"/api/v1/kardex/articulos/{articulo.id}/asignar-area",
            headers=headers, json={"area_id": area.id, "cantidad": cantidad,
                "encargado_id": usuario_admin.id,
                "referencia_documento": "ACTA-UBICACION",
                "justificacion": "Conteo y ubicación verificados"}).status_code == 200
    return origen, destino


def datos(origen, destino, encargado, **cambios):
    return {"solicitud_id": str(uuid4()), "area_origen_id": origen.id,
            "area_destino_id": destino.id, "cantidad": 3,
            "encargado_id": encargado.id,
            "referencia_documento": "ACTA-TRASLADO-01", **cambios}


def cantidades(db_session, articulo_id):
    return {e.area_id: e.cantidad for e in db_session.query(Existencia).filter_by(
        activo_id=articulo_id).all()}


def test_transferencia_atomica_conserva_total_e_historial_y_reintento(
    client, db_session, usuario_admin, usuario_operador, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/transferencias"
    payload = datos(origen, destino, usuario_admin)
    headers = auth_headers(usuario_operador)

    primera = client.post(ruta, headers=headers, json=payload)
    repetida = client.post(ruta, headers=headers, json=payload)
    colision = client.post(ruta, headers=headers, json={**payload, "cantidad": 2})

    assert primera.status_code == repetida.status_code == 200
    registro = primera.json()["registro"]
    assert registro["id"] == repetida.json()["registro"]["id"]
    assert registro["solicitud_id"] == payload["solicitud_id"]
    assert registro["encargado_id"] == usuario_admin.id
    assert registro["registrado_por"] == usuario_operador.id
    assert registro["referencia_documento"] == "ACTA-TRASLADO-01"
    assert registro["ocurrido_en"] and registro["registrado_en"]
    assert primera.json()["distribucion"]["total_institucional"] == 10
    assert colision.status_code == 409
    assert cantidades(db_session, articulo.id) == {origen.id: 3, destino.id: 7}
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 10
    assert db_session.query(MovimientoKardex).count() == 0
    assert db_session.query(TransferenciaArea).count() == 1
    assert db_session.query(AuditoriaSistema).filter_by(
        accion="transferir_existencia_area").count() == 1
    historial = client.get(ruta, headers=auth_headers(usuario_admin))
    assert historial.status_code == 200
    assert historial.json()[0]["area_origen"] == origen.nombre
    assert historial.json()[0]["area_destino"] == destino.nombre


def test_transferencia_invalida_no_mueve_unidades(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/transferencias"
    headers = auth_headers(usuario_admin)
    casos = [
        (datos(origen, destino, usuario_admin, cantidad=7), 409),
        (datos(origen, destino, usuario_admin, area_destino_id=origen.id), 422),
        (datos(origen, destino, usuario_admin, fecha_operacion=(
            datetime.now(UTC) - timedelta(days=1)).isoformat()), 409),
        (datos(origen, destino, usuario_admin, fecha_operacion=(
            datetime.now(UTC) + timedelta(hours=1)).isoformat()), 422),
        (datos(origen, destino, usuario_admin, referencia_documento=" "), 422),
    ]
    for payload, codigo in casos:
        respuesta = client.post(ruta, headers=headers, json=payload)
        assert respuesta.status_code == codigo, respuesta.json()
    assert cantidades(db_session, articulo.id) == {origen.id: 6, destino.id: 4}
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 10
    assert db_session.query(TransferenciaArea).count() == 0


def test_fallo_de_auditoria_revierte_ambas_areas(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)

    def fallar(_mapper, _connection, _target):
        raise RuntimeError("Auditoría no disponible")

    event.listen(AuditoriaSistema, "before_insert", fallar)
    try:
        with pytest.raises(RuntimeError, match="Auditoría no disponible"):
            client.post(f"/api/v1/kardex/articulos/{articulo.id}/transferencias",
                headers=auth_headers(usuario_admin),
                json=datos(origen, destino, usuario_admin))
    finally:
        event.remove(AuditoriaSistema, "before_insert", fallar)
        db_session.rollback()
    assert cantidades(db_session, articulo.id) == {origen.id: 6, destino.id: 4}
    assert db_session.query(TransferenciaArea).count() == 0
