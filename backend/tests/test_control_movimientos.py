from datetime import datetime
from zoneinfo import ZoneInfo
import pytest

from app.models.auditoria import AuditoriaSistema
from app.models.inventario import AperturaInventario
from app.models.kardex import MovimientoKardex
from app.services.control_movimientos import evaluar_movimiento, firma_confirmacion, validar_operacion
from test_kardex import auth_headers, activos_prueba


def codigos(**kwargs):
    return {a["codigo"] for a in evaluar_movimiento(**kwargs)}


def test_reglas_distinguen_salida_total_cantidad_atipica_y_horario():
    fecha = datetime(2026, 10, 7, 21, 30, tzinfo=ZoneInfo("America/La_Paz"))
    avisos = codigos(tipo="salida", cantidad=1000, saldo=1000,
                    fecha_local=fecha, cantidades_previas=[10, 12, 10, 11, 9])
    assert avisos == {"AGOTA_STOCK", "CANTIDAD_EXTREMA",
                      "CANTIDAD_ATIPICA", "FUERA_HORARIO"}
    normal = codigos(tipo="ingreso", cantidad=5, saldo=100,
                    fecha_local=fecha.replace(hour=12), cantidades_previas=[5] * 5)
    assert normal == set()
    assert "SALIDA_MAYORITARIA" in codigos(
        tipo="salida", cantidad=8, saldo=10,
        fecha_local=fecha.replace(hour=12), cantidades_previas=[])


def test_operaciones_conocidas_respetan_direccion_y_evidencia():
    base = dict(receptor=None, feria_id=None, ciudad_feria=None, motivo_baja=None)
    assert "salida" in validar_operacion(tipo="ingreso", operacion="Ventas", **base)
    assert "ingreso" in validar_operacion(tipo="salida", operacion="Inventario / Compra", **base)
    assert "receptor" in validar_operacion(tipo="salida", operacion="Consignación", **base)
    assert "motivo" in validar_operacion(tipo="salida", operacion="Baja / Pérdida", **base)
    assert "feria" in validar_operacion(tipo="salida", operacion="Salida a Feria",
        **{**base, "receptor": "Galería", "ciudad_feria": None},
        receptor_tipo="INSTITUCION")
    assert "receptor" in validar_operacion(tipo="salida", operacion="Ventas", **base)
    assert "persona o institución" in validar_operacion(
        tipo="salida", operacion="Ventas", **{**base, "receptor": "Centro Cultural"})
    assert validar_operacion(tipo="salida", operacion="Ventas",
        **{**base, "receptor": "Centro Cultural"}, receptor_tipo="INSTITUCION",
        referencia_documento="FACT-TEST") is None
    assert "documento" in validar_operacion(tipo="salida", operacion="Ventas",
        **{**base, "receptor": "Público general"}, receptor_tipo="PUBLICO_GENERAL")


def test_venta_conserva_destinatario_y_responsables(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    headers = auth_headers(usuario_admin)
    assert client.post(f"/api/v1/kardex/articulos/{articulo.id}/apertura",
        headers=headers, json={"cantidad": 20, "referencia_documento": "ACTA-01",
            "justificacion": "Conteo físico verificado", "conteo_verificado": True}).status_code == 200
    payload = {"articulo_id": articulo.id,
               "solicitud_id": "22222222-2222-4222-8222-222222222222",
               "tipo": "salida", "cantidad": 2,
               "nodo_grafo": "Ventas", "tipo_operacion": "Ventas",
               "encargado_id": usuario_admin.id, "receptor": "Biblioteca Municipal",
               "receptor_tipo": "INSTITUCION", "referencia_documento": "FACT-10"}
    sin_receptor = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
                               json={**payload, "receptor": "   "})
    assert sin_receptor.status_code == 422
    assert db_session.query(MovimientoKardex).count() == 0
    r = client.post("/api/v1/kardex/movimiento-actual", headers=headers, json=payload)
    assert r.status_code == 200
    assert r.json()["receptor"] == "Biblioteca Municipal"
    assert r.json()["receptor_tipo"] == "INSTITUCION"
    assert r.json()["encargado_id"] == usuario_admin.id
    assert r.json()["usuario_registrador_id"] == usuario_admin.id


def test_firma_caduca_con_alerta_o_historial_distinto_pero_no_por_segundos():
    aviso = {"codigo": "FUERA_HORARIO", "nivel": "medio", "mensaje": "Fuera de horario",
             "datos": {"fecha_local": "2026-10-07T21:30:01-04:00", "zona": "America/La_Paz"}}
    base = dict(payload={"articulo_id": 1, "cantidad": 8}, usuario_id=2,
                saldo=10, hora_local="2026-10-07T21", ultimo_movimiento_id=9)
    firma = firma_confirmacion("clave", alertas=[aviso], **base)
    aviso_minuto_despues = {**aviso, "datos": {**aviso["datos"], "fecha_local": "2026-10-07T21:31:00-04:00"}}
    assert firma_confirmacion("clave", alertas=[aviso_minuto_despues], **base) == firma
    assert firma_confirmacion("clave", alertas=[aviso], **{**base, "ultimo_movimiento_id": 10}) != firma
    aviso_distinto = {**aviso, "datos": {**aviso["datos"], "zona": "otra"}}
    assert firma_confirmacion("clave", alertas=[aviso_distinto], **base) != firma


def test_api_rechaza_venta_como_ingreso_sin_modificar_stock(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    cabecera = auth_headers(usuario_admin)
    assert client.post(
        f"/api/v1/kardex/articulos/{articulo.id}/apertura", headers=cabecera,
        json={"cantidad": 10, "referencia_documento": "ACTA-CONTROL",
              "justificacion": "Conteo físico verificado", "conteo_verificado": True},
    ).status_code == 200
    respuesta = client.post("/api/v1/kardex/movimiento-actual", headers=cabecera,
                            json={"articulo_id": articulo.id,
                                  "solicitud_id": "33333333-3333-4333-8333-333333333333",
                                  "tipo": "ingreso",
                                  "cantidad": 2, "nodo_grafo": "Ventas",
                                  "tipo_operacion": "Ventas"})
    assert respuesta.status_code == 422
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 10
    assert db_session.query(MovimientoKardex).count() == 0


def test_devolucion_pendiente_no_incrementa_stock_sin_salida_vinculada(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    cabecera = auth_headers(usuario_admin)
    assert client.post(
        f"/api/v1/kardex/articulos/{articulo.id}/apertura", headers=cabecera,
        json={"cantidad": 10, "referencia_documento": "ACTA-CONTROL",
              "justificacion": "Conteo físico verificado", "conteo_verificado": True},
    ).status_code == 200
    respuesta = client.post("/api/v1/kardex/movimiento-actual", headers=cabecera,
                            json={"articulo_id": articulo.id,
                                  "solicitud_id": "44444444-4444-4444-8444-444444444444",
                                  "tipo": "ingreso",
                                  "cantidad": 2, "nodo_grafo": "Devolución",
                                  "tipo_operacion": "Devolución",
                                  "referencia_documento": "ACTA-DEVOLUCION"})
    assert respuesta.status_code == 409
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 10
    assert db_session.query(MovimientoKardex).count() == 0


@pytest.mark.parametrize("operacion", ["Consignación", "Salida a Feria", "Préstamo a Exposición"])
def test_custodia_temporal_no_se_registra_como_salida_definitiva(
    client, db_session, usuario_admin, activos_prueba, operacion,
):
    articulo, _ = activos_prueba
    cabecera = auth_headers(usuario_admin)
    assert client.post(
        f"/api/v1/kardex/articulos/{articulo.id}/apertura", headers=cabecera,
        json={"cantidad": 10, "referencia_documento": "ACTA-CONTROL",
              "justificacion": "Conteo físico verificado", "conteo_verificado": True},
    ).status_code == 200
    respuesta = client.post("/api/v1/kardex/movimiento-actual", headers=cabecera,
                            json={"articulo_id": articulo.id,
                                  "solicitud_id": "55555555-5555-4555-8555-555555555555",
                                  "tipo": "salida",
                                  "cantidad": 2, "nodo_grafo": operacion,
                                  "tipo_operacion": operacion,
                                  "receptor": "Museo de prueba", "receptor_tipo": "INSTITUCION",
                                  "referencia_documento": "ACTA-CUSTODIA"})
    assert respuesta.status_code == 409
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 10
    assert db_session.query(MovimientoKardex).count() == 0


def test_aviso_requiere_confirmacion_y_justificacion_sin_escribir_antes(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    cabecera = auth_headers(usuario_admin)
    apertura = client.post(
        f"/api/v1/kardex/articulos/{articulo.id}/apertura", headers=cabecera,
        json={"cantidad": 10, "referencia_documento": "ACTA-CONTROL",
              "justificacion": "Conteo físico verificado", "conteo_verificado": True},
    )
    assert apertura.status_code == 200
    payload = {"articulo_id": articulo.id,
               "solicitud_id": "66666666-6666-4666-8666-666666666666",
               "tipo": "salida", "cantidad": 10,
               "nodo_grafo": "Ventas", "encargado_id": usuario_admin.id,
               "referencia_documento": "ACTA-CONTROL"}
    previa = client.post("/api/v1/kardex/movimiento-actual",
                         headers=cabecera, json=payload)
    assert previa.status_code == 409
    detalle = previa.json()["detail"]
    assert detalle["codigo"] == "ALERTAS_CONTROL"
    assert [a["codigo"] for a in detalle["alertas"]] == ["AGOTA_STOCK"]
    assert db_session.query(MovimientoKardex).count() == 0
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 10

    payload["confirmacion_alertas"] = detalle["firma_confirmacion"]
    payload["motivo_alertas"] = "corto"
    assert client.post("/api/v1/kardex/movimiento-actual",
                       headers=cabecera, json=payload).status_code == 422
    payload["motivo_alertas"] = "Entrega total autorizada mediante acta"
    final = client.post("/api/v1/kardex/movimiento-actual",
                        headers=cabecera, json=payload)
    assert final.status_code == 200
    movimiento = final.json()
    assert movimiento["saldo_registrado"] == 0
    assert movimiento["alertas_control"][0]["codigo"] == "AGOTA_STOCK"
    assert movimiento["justificacion_alertas"] == payload["motivo_alertas"]
    assert movimiento["registrado_en"] is not None
    evento = db_session.query(AuditoriaSistema).filter_by(
        accion="crear_movimiento_inventario", recurso_id=movimiento["id"]).one()
    assert evento.detalle["alertas_control"] == ["AGOTA_STOCK"]


def test_confirmacion_no_autoriza_otra_cantidad(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    cabecera = auth_headers(usuario_admin)
    assert client.post(
        f"/api/v1/kardex/articulos/{articulo.id}/apertura", headers=cabecera,
        json={"cantidad": 10, "referencia_documento": "ACTA-CONTROL",
              "justificacion": "Conteo físico verificado", "conteo_verificado": True},
    ).status_code == 200
    payload = {"articulo_id": articulo.id,
               "solicitud_id": "77777777-7777-4777-8777-777777777777",
               "tipo": "salida", "cantidad": 8,
               "nodo_grafo": "Ventas", "referencia_documento": "ACTA-CONTROL"}
    previa = client.post("/api/v1/kardex/movimiento-actual",
                         headers=cabecera, json=payload).json()["detail"]
    payload.update(cantidad=9, confirmacion_alertas=previa["firma_confirmacion"],
                   motivo_alertas="Salida autorizada por la dirección")
    cambiada = client.post("/api/v1/kardex/movimiento-actual",
                           headers=cabecera, json=payload)
    assert cambiada.status_code == 409
    assert cambiada.json()["detail"]["codigo"] == "ALERTAS_CONTROL"
    assert db_session.query(MovimientoKardex).count() == 0
