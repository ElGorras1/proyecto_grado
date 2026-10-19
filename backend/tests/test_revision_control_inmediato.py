"""Controles del contexto operativo y confirmaciones que no alteran la vista previa."""
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from app.core.config import settings
from app.models.auditoria import AuditoriaSistema
from app.models.inventario import AperturaInventario, TransferenciaArea
from app.models.kardex import LoteCarga, MovimientoKardex
from app.services.control_movimientos import evaluar_movimiento, cantidades_comparables, firma_confirmacion
from test_kardex import activos_prueba, auth_headers, crear_movimiento, usuario_auditor
from test_transferencias_area import escenario, datos, cantidades
from test_ajustes_operativos import prueba_movimiento
from test_custodias_externas import entrega, evento


@pytest.mark.parametrize("hora,minuto,fuera", [(6, 59, True), (7, 0, False), (19, 59, False), (20, 0, True)])
def test_limites_horario(hora, minuto, fuera):
    avisos = evaluar_movimiento(tipo="ingreso", cantidad=1, saldo=10,
        fecha_local=datetime(2026, 10, 8, hora, minuto, tzinfo=ZoneInfo("America/La_Paz")), cantidades_previas=[])
    assert ("FUERA_HORARIO" in {a["codigo"] for a in avisos}) is fuera


def test_hora_del_hecho_y_registro_tardio_son_distintos_del_reloj_de_carga():
    ahora = datetime(2026, 10, 8, 12, tzinfo=ZoneInfo("America/La_Paz"))
    parametros = dict(tipo="ingreso", cantidad=1, saldo=10, cantidades_previas=[])
    avisos = evaluar_movimiento(**parametros, fecha_local=ahora,
        fecha_operacion_local=ahora.replace(day=6, hour=22))
    assert {a["codigo"] for a in avisos} == {"OPERACION_FUERA_HORARIO", "REGISTRO_TARDIO"}
    # Sin hora declarada se usa el instante del registro: los segundos no deben
    # cambiar la firma de una confirmación fuera de horario.
    noche = ahora.replace(hour=21)
    uno = evaluar_movimiento(**parametros, fecha_local=noche)
    dos = evaluar_movimiento(**parametros, fecha_local=noche + timedelta(seconds=30))
    firma = dict(payload={"fecha_operacion": None}, usuario_id=1, saldo=10,
                 hora_local=noche.strftime("%Y-%m-%dT%H"), ultimo_movimiento_id=0)
    assert firma_confirmacion("clave", alertas=uno, **firma) == firma_confirmacion("clave", alertas=dos, **firma)


def test_comparables_excluyen_ocr_otros_tipos_areas_y_asientos_de_rectificacion(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    filas = []
    for _ in range(5):
        m = crear_movimiento(db_session, articulo_id=articulo.id, fecha=date.today(), salidas=1, saldo=9)
        m.tipo_operacion = "Ventas"; m.area_operativa_id = origen.id; filas.append(m)
    for operacion, area in (("Baja / Pérdida", origen.id), ("Ventas", destino.id)):
        m = crear_movimiento(db_session, articulo_id=articulo.id, fecha=date.today(), salidas=999, saldo=9)
        m.tipo_operacion = operacion; m.area_operativa_id = area
    lote = LoteCarga(total_imagenes=1); db_session.add(lote); db_session.flush()
    m = crear_movimiento(db_session, articulo_id=articulo.id, lote_id=lote.id, fecha=date(2025, 1, 1), salidas=900, saldo=9)
    m.tipo_operacion = "Ventas"; m.area_operativa_id = origen.id
    correccion = crear_movimiento(db_session, articulo_id=articulo.id, fecha=date.today(), salidas=1, saldo=8)
    correccion.tipo_operacion = "Rectificación operativa"; correccion.corrige_movimiento_id = filas[0].id
    correccion.cantidad_corregida = 2; db_session.commit()
    anteriores = cantidades_comparables(
        db_session, articulo_id=articulo.id, ultimo_moderno_id=0, tipo="salida", operacion="Ventas", area_id=origen.id)
    assert sorted(anteriores) == [1, 1, 1, 1, 2]


def test_vaciar_area_no_pasa_inadvertido_y_superar_area_sigue_bloqueado(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, _ = escenario(client, db_session, usuario_admin, articulo)
    payload = {"solicitud_id": str(uuid4()), "articulo_id": articulo.id, "tipo": "salida", "cantidad": 6,
               "tipo_operacion": "Ventas", "nodo_grafo": "Ventas", "area_operativa_id": origen.id,
               "receptor": "Biblioteca", "receptor_tipo": "INSTITUCION", "referencia_documento": "FACT-AREA-01"}
    headers = auth_headers(usuario_admin)
    previa = client.post("/api/v1/kardex/movimiento-actual", headers=headers, json=payload)
    assert previa.status_code == 409
    detalle = previa.json()["detail"]
    assert {a["codigo"] for a in detalle["alertas"]} == {"AGOTA_AREA"}
    assert cantidades(db_session, articulo.id)[origen.id] == 6
    assert db_session.query(MovimientoKardex).count() == 0
    exceso = client.post("/api/v1/kardex/movimiento-actual", headers=headers, json={**payload, "cantidad": 7})
    assert exceso.status_code == 409 and isinstance(exceso.json()["detail"], str)
    final = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
        json={**payload, "confirmacion_alertas": detalle["firma_confirmacion"], "motivo_alertas": "Venta íntegra de las unidades del área autorizada"})
    assert final.status_code == 200 and final.json()["saldo_registrado"] == 4


def test_transferencia_alertada_se_revisa_si_cambia_stock_y_persiste_justificacion(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    headers = auth_headers(usuario_admin)
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/transferencias"
    payload = datos(origen, destino, usuario_admin, cantidad=6)
    previa = client.post(ruta, headers=headers, json=payload)
    assert previa.status_code == 409
    d = previa.json()["detail"]
    assert {a["codigo"] for a in d["alertas"]} == {"AGOTA_AREA_POR_TRANSFERENCIA"}
    assert cantidades(db_session, articulo.id) == {origen.id: 6, destino.id: 4}
    assert db_session.query(TransferenciaArea).count() == 0
    prueba_movimiento(client, usuario_admin, articulo, destino, tipo="ingreso", cantidad=1)
    motivo = "Traslado completo aprobado con verificación de ambas áreas"
    revisada = client.post(ruta, headers=headers, json={**payload, "confirmacion_alertas": d["firma_confirmacion"], "motivo_alertas": motivo})
    assert revisada.status_code == 409
    nuevo = revisada.json()["detail"]["firma_confirmacion"]
    assert nuevo != d["firma_confirmacion"]
    confirmada = {**payload, "confirmacion_alertas": nuevo, "motivo_alertas": motivo}
    final = client.post(ruta, headers=headers, json=confirmada)
    assert final.status_code == 200, final.text
    repetida = client.post(ruta, headers=headers, json=confirmada)
    assert repetida.status_code == 200 and repetida.json()["registro"]["id"] == final.json()["registro"]["id"]
    assert final.json()["registro"]["justificacion_alertas"] == motivo
    assert cantidades(db_session, articulo.id) == {origen.id: 0, destino.id: 11}
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 11
    assert db_session.query(AuditoriaSistema).filter_by(accion="transferir_existencia_area").one().detalle["alertas_control"] == ["AGOTA_AREA_POR_TRANSFERENCIA"]
    libro = client.get(f"/api/v1/kardex/articulos/{articulo.id}/kardex-digital", headers=headers).json()
    assert libro["integridad"] is True
    assert libro["eventos"][-1]["justificacion_alertas"] == motivo


def test_posible_duplicado_permite_excepcion_y_distingue_reintento_y_ventana(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, _ = escenario(client, db_session, usuario_admin, articulo)
    venta = prueba_movimiento(client, usuario_admin, articulo, origen, cantidad=1)
    ruta = "/api/v1/kardex/movimiento-actual"
    headers = auth_headers(usuario_admin)
    payload = {"solicitud_id": str(uuid4()), "articulo_id": articulo.id, "tipo": "salida", "cantidad": 1,
               "tipo_operacion": "Ventas", "nodo_grafo": "Ventas", "area_operativa_id": origen.id,
               "receptor": "Biblioteca", "receptor_tipo": "INSTITUCION", "referencia_documento": " fact-prueba-01 "}
    previa = client.post(ruta, headers=headers, json=payload)
    assert previa.status_code == 409
    d = previa.json()["detail"]
    assert {a["codigo"] for a in d["alertas"]} == {"POSIBLE_DUPLICADO"}
    assert d["alertas"][0]["datos"]["registros_previos"] == [venta["id"]]
    assert cantidades(db_session, articulo.id)[origen.id] == 5
    payload.update(confirmacion_alertas=d["firma_confirmacion"], motivo_alertas="Segunda entrega parcial del mismo comprobante verificada")
    final = client.post(ruta, headers=headers, json=payload)
    assert final.status_code == 200
    assert client.post(ruta, headers=headers, json=payload).json()["id"] == final.json()["id"]
    assert db_session.query(MovimientoKardex).count() == 2
    for m in db_session.query(MovimientoKardex):
        m.registrado_en = datetime.now(UTC) - timedelta(minutes=10)
    db_session.commit()
    payload.update(solicitud_id=str(uuid4()), confirmacion_alertas=None, motivo_alertas="")
    assert client.post(ruta, headers=headers, json=payload).status_code == 200


def test_retornos_repetidos_se_justifican_sin_superar_custodia(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/custodias-externas"
    headers = auth_headers(usuario_admin)
    c = client.post(ruta, headers=headers, json=entrega(articulo, origen, usuario_admin)).json()["registro"]["id"]
    payload = evento(usuario_admin, tipo="RETORNO", area_destino_id=destino.id)
    assert client.post(f"{ruta}/{c}/eventos", headers=headers, json=payload).status_code == 200
    payload["solicitud_id"] = str(uuid4())
    previa = client.post(f"{ruta}/{c}/eventos", headers=headers, json=payload)
    assert previa.status_code == 409
    d = previa.json()["detail"]
    assert {a["codigo"] for a in d["alertas"]} == {"POSIBLE_DUPLICADO"}
    payload.update(confirmacion_alertas=d["firma_confirmacion"], motivo_alertas="Recepción en dos entregas parciales del acta verificada")
    final = client.post(f"{ruta}/{c}/eventos", headers=headers, json=payload)
    assert final.status_code == 200 and final.json()["custodia"]["cantidad_fuera"] == 1


@pytest.mark.parametrize("clase", ["MOVIMIENTO", "TRANSFERENCIA"])
def test_confirmacion_caducada_no_guarda_y_permite_revisar_la_misma_solicitud(
    clase, client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    headers = auth_headers(usuario_admin)
    if clase == "MOVIMIENTO":
        ruta = "/api/v1/kardex/movimiento-actual"
        payload = {"solicitud_id": str(uuid4()), "articulo_id": articulo.id,
            "tipo": "salida", "cantidad": 1, "tipo_operacion": "Ventas",
            "nodo_grafo": "Ventas", "area_operativa_id": origen.id,
            "receptor": "Biblioteca", "receptor_tipo": "INSTITUCION",
            "referencia_documento": "FACT-VENTANA-01"}
        modelo = MovimientoKardex
    else:
        ruta = f"/api/v1/kardex/articulos/{articulo.id}/transferencias"
        payload = datos(origen, destino, usuario_admin, cantidad=1)
        modelo = TransferenciaArea
    assert client.post(ruta, headers=headers, json=payload).status_code == 200
    payload["solicitud_id"] = str(uuid4())
    previa = client.post(ruta, headers=headers, json=payload)
    assert previa.status_code == 409
    detalle = previa.json()["detail"]
    assert {a["codigo"] for a in detalle["alertas"]} == {"POSIBLE_DUPLICADO"}
    anterior = db_session.query(modelo).one()
    anterior.registrado_en = datetime.now(UTC) - timedelta(minutes=10)
    db_session.commit()
    payload.update(confirmacion_alertas=detalle["firma_confirmacion"],
                   motivo_alertas="Segunda entrega del mismo documento verificada")
    vencida = client.post(ruta, headers=headers, json=payload)
    assert vencida.status_code == 409
    assert vencida.json()["detail"]["codigo"] == "CONTROL_DESACTUALIZADO"
    assert db_session.query(modelo).count() == 1
    assert cantidades(db_session, articulo.id)[origen.id] == 5
    payload.update(confirmacion_alertas=None, motivo_alertas="")
    assert client.post(ruta, headers=headers, json=payload).status_code == 200
    assert db_session.query(modelo).count() == 2


def test_registro_tardio_requiere_revision_y_politica_es_consultable(
    client, db_session, usuario_admin, usuario_auditor, activos_prueba, monkeypatch,
):
    articulo, _ = activos_prueba
    origen, _ = escenario(client, db_session, usuario_admin, articulo)
    apertura = db_session.get(AperturaInventario, articulo.id)
    apertura.aprobado_en = datetime.now(UTC) - timedelta(days=4); db_session.commit()
    payload = {"solicitud_id": str(uuid4()), "articulo_id": articulo.id, "tipo": "ingreso", "cantidad": 1,
               "tipo_operacion": "Inventario / Compra", "nodo_grafo": "Inventario / Compra", "area_operativa_id": origen.id,
               "referencia_documento": "FACT-TARDIA-01", "fecha_operacion": (datetime.now(UTC) - timedelta(days=2)).isoformat()}
    previa = client.post("/api/v1/kardex/movimiento-actual", headers=auth_headers(usuario_admin), json=payload)
    assert previa.status_code == 409
    assert {a["codigo"] for a in previa.json()["detail"]["alertas"]} == {"REGISTRO_TARDIO"}
    assert db_session.query(MovimientoKardex).count() == 0
    monkeypatch.setattr(settings, "CONTROL_PORCENTAJE_MAYORITARIO", 70)
    d = client.get("/api/v1/kardex/politica-control", headers=auth_headers(usuario_auditor)).json()
    assert d["porcentaje_mayoritario"] == 70 and d["estado"] == "PROVISIONAL"
    assert client.get("/api/v1/kardex/politica-control").status_code == 401
