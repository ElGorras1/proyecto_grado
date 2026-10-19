"""La fecha declarada del hecho no debe confundirse con su registro digital."""
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo
from uuid import uuid4

from app.models.auditoria import AuditoriaSistema
from app.models.inventario import AperturaInventario
from app.models.kardex import LoteCarga, MovimientoKardex
from test_kardex import activos_prueba, auth_headers, crear_movimiento


def abrir(client, usuario, articulo):
    respuesta = client.post(
        f"/api/v1/kardex/articulos/{articulo.id}/apertura",
        headers=auth_headers(usuario),
        json={"cantidad": 10, "referencia_documento": "ACTA-APERTURA",
              "justificacion": "Conteo físico verificado", "conteo_verificado": True},
    )
    assert respuesta.status_code == 200


def payload(articulo, **cambios):
    return {"articulo_id": articulo.id, "solicitud_id": str(uuid4()),
            "tipo": "ingreso", "cantidad": 2,
            "nodo_grafo": "Inventario / Compra",
            "tipo_operacion": "Inventario / Compra",
            "referencia_documento": "FACT-2026-10", **cambios}


def test_operacion_atrasada_conserva_fecha_real_y_hora_de_registro(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    abrir(client, usuario_admin, articulo)
    apertura = db_session.get(AperturaInventario, articulo.id)
    apertura.aprobado_en = datetime.now(UTC) - timedelta(days=2)
    db_session.commit()
    fecha_operacion = datetime.now(UTC) - timedelta(hours=12)

    respuesta = client.post("/api/v1/kardex/movimiento-actual",
        headers=auth_headers(usuario_admin),
        json=payload(articulo, fecha_operacion=fecha_operacion.isoformat()))

    assert respuesta.status_code == 200
    movimiento = respuesta.json()
    assert movimiento["fecha_movimiento"] == fecha_operacion.astimezone(
        ZoneInfo("America/La_Paz")).date().isoformat()
    ocurrio = datetime.fromisoformat(movimiento["ocurrido_en"])
    registrado = datetime.fromisoformat(movimiento["registrado_en"])
    # SQLite pierde la zona en las pruebas; PostgreSQL conserva timestamptz.
    if ocurrio.tzinfo is None:
        ocurrio = ocurrio.replace(tzinfo=UTC)
    if registrado.tzinfo is None:
        registrado = registrado.replace(tzinfo=UTC)
    assert abs(ocurrio - fecha_operacion) < timedelta(seconds=1)
    assert registrado > fecha_operacion
    assert movimiento["referencia_documento"] == "FACT-2026-10"
    assert movimiento["area_operativa_id"] is None
    assert movimiento["encargado_id"] == usuario_admin.id
    assert movimiento["usuario_registrador_id"] == usuario_admin.id
    assert movimiento["saldo_registrado"] == 12
    evento = db_session.query(AuditoriaSistema).filter_by(
        accion="crear_movimiento_inventario", recurso_id=movimiento["id"]).one()
    assert evento.detalle["ocurrido_en"] == fecha_operacion.isoformat()
    assert evento.detalle["referencia_documento"] == "FACT-2026-10"


def test_rechaza_operaciones_anteriores_al_corte_y_futuras_sin_tocar_stock(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    abrir(client, usuario_admin, articulo)
    headers = auth_headers(usuario_admin)
    anterior = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
        json=payload(articulo, fecha_operacion=(datetime.now(UTC) - timedelta(days=1)).isoformat()))
    futura = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
        json=payload(articulo, fecha_operacion=(datetime.now(UTC) + timedelta(hours=1)).isoformat()))
    sin_zona = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
        json=payload(articulo, fecha_operacion="2026-10-08T10:00:00"))

    assert anterior.status_code == 409
    assert futura.status_code == 422
    assert sin_zona.status_code == 422
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 10
    assert db_session.query(MovimientoKardex).count() == 0


def test_referencia_documental_obligatoria_en_toda_operacion_nueva(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    abrir(client, usuario_admin, articulo)
    sin_documento = payload(articulo)
    del sin_documento["referencia_documento"]
    for datos in (sin_documento, payload(articulo, referencia_documento="  ")):
        respuesta = client.post("/api/v1/kardex/movimiento-actual",
            headers=auth_headers(usuario_admin), json=datos)
        assert respuesta.status_code == 422
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 10
    assert db_session.query(MovimientoKardex).count() == 0


def test_primera_operacion_activa_base_historica_con_segundos_precisos(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    lote = LoteCarga(total_imagenes=1)
    db_session.add(lote)
    db_session.commit()
    crear_movimiento(db_session, articulo_id=articulo.id, lote_id=lote.id,
        fecha=date(2025, 12, 31), saldo=5, ingresos=5,
        numero_pagina=1, orden_fila=1)
    ocurrio = datetime.now(UTC) - timedelta(seconds=15)

    respuesta = client.post("/api/v1/kardex/movimiento-actual",
        headers=auth_headers(usuario_admin),
        json=payload(articulo, fecha_operacion=ocurrio.isoformat()))

    assert respuesta.status_code == 200, respuesta.json()
    apertura = db_session.get(AperturaInventario, articulo.id)
    corte = apertura.aprobado_en
    if corte.tzinfo is None:
        corte = corte.replace(tzinfo=UTC)
    assert abs(corte - ocurrio) < timedelta(seconds=1)
    assert apertura.cantidad_inicial == 5
    assert apertura.cantidad_actual == 7
