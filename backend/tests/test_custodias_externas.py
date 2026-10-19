"""La custodia fuera de la institución no reduce el patrimonio hasta la venta."""
import csv
import io
from uuid import uuid4

from app.models.activos import Existencia
from app.models.auditoria import AuditoriaSistema
from app.models.inventario import AperturaInventario, CustodiaExterna, EventoCustodiaExterna
from app.models.kardex import MovimientoKardex
from app.core.config import settings
from test_kardex import activos_prueba, auth_headers
from test_transferencias_area import escenario


def entrega(articulo, origen, encargado, *, tipo="FERIA", **cambios):
    return {"solicitud_id": str(uuid4()), "tipo": tipo,
            "area_origen_id": origen.id, "receptor_nombre": "Centro Cultural",
            "receptor_tipo": "INSTITUCION", "ubicacion_externa": "Puesto 12",
            "ciudad": "Cochabamba" if tipo == "FERIA" else None,
            "cantidad": 3, "encargado_id": encargado.id,
            "referencia_documento": "ACTA-ENTREGA-01", **cambios}


def evento(encargado, *, tipo="VENTA", **cambios):
    return {"solicitud_id": str(uuid4()), "tipo": tipo,
            "cantidad": 1, "encargado_id": encargado.id,
            "comprador": "Biblioteca" if tipo == "VENTA" else None,
            "referencia_documento": "FACT-01" if tipo == "VENTA" else "ACTA-RET-01",
            **cambios}


def test_feria_conserva_total_y_separa_venta_de_retorno(
    client, db_session, usuario_admin, usuario_operador, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    headers = auth_headers(usuario_operador)
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/custodias-externas"
    datos = entrega(articulo, origen, usuario_admin)
    primera = client.post(ruta, headers=headers, json=datos)
    repetida = client.post(ruta, headers=headers, json=datos)
    assert primera.status_code == repetida.status_code == 200, primera.text
    custodia = primera.json()["registro"]
    assert custodia["id"] == repetida.json()["registro"]["id"]
    assert custodia["cantidad_fuera"] == 3
    assert custodia["total_institucional_entrega"] == 10
    assert primera.json()["distribucion"]["en_custodia_externa"] == 3
    assert primera.json()["distribucion"]["total_institucional"] == 10
    assert client.post(ruta, headers=headers, json={**datos, "cantidad": 2}).status_code == 409
    assert client.post(ruta, headers=headers, json=entrega(articulo, origen,
        usuario_admin, cantidad=4)).status_code == 409

    ruta_eventos = f"{ruta}/{custodia['id']}/eventos"
    venta = evento(usuario_admin)
    vendida = client.post(ruta_eventos, headers=headers, json=venta)
    reintento = client.post(ruta_eventos, headers=headers, json=venta)
    assert vendida.status_code == reintento.status_code == 200, vendida.text
    assert vendida.json()["registro"]["id"] == reintento.json()["registro"]["id"]
    assert vendida.json()["registro"]["total_institucional_despues"] == 9
    assert vendida.json()["custodia"]["cantidad_fuera"] == 2
    assert client.post(ruta_eventos, headers=headers, json={**venta,
        "cantidad": 2, "solicitud_id": str(uuid4())}).status_code == 200
    # La feria ya vendió las tres unidades; una recepción adicional no puede crear stock.
    assert client.post(ruta_eventos, headers=headers,
        json=evento(usuario_admin, tipo="RETORNO", area_destino_id=destino.id)).status_code == 409
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 7
    assert db_session.get(AperturaInventario, articulo.id).cantidad_custodia_externa == 0
    assert db_session.query(CustodiaExterna).count() == 1
    assert db_session.query(EventoCustodiaExterna).count() == 2
    assert db_session.query(MovimientoKardex).count() == 0
    assert {e.area_id: e.cantidad for e in db_session.query(Existencia).filter_by(
        activo_id=articulo.id).all()} == {origen.id: 3, destino.id: 4}
    assert db_session.query(AuditoriaSistema).filter_by(
        accion="entregar_custodia_externa").count() == 1
    assert db_session.query(AuditoriaSistema).filter_by(
        accion="vender_desde_custodia").count() == 2
    libro = client.get(f"/api/v1/kardex/articulos/{articulo.id}/kardex-digital",
                       headers=headers).json()
    assert libro["saldo_final"] == 7 and libro["integridad"] is True
    assert [e["clase"] for e in libro["eventos"]] == [
        "CUSTODIA_ENTREGA", "CUSTODIA_VENTA", "CUSTODIA_VENTA"]
    archivo = client.get(f"/api/v1/kardex/articulos/{articulo.id}/kardex-digital.csv",
                         headers=headers)
    assert archivo.status_code == 200
    filas = list(csv.DictReader(io.StringIO(archivo.text.lstrip("\ufeff")), delimiter=";"))
    assert [fila["tipo"] for fila in filas] == [
        "BASE", "CUSTODIA_ENTREGA", "CUSTODIA_VENTA", "CUSTODIA_VENTA"]
    assert filas[1]["receptor"] == "Centro Cultural"
    assert filas[-1]["saldo_institucional"] == "7"
    assert client.get(ruta, headers=headers).json()[0]["estado"] == "CERRADA"
    conciliacion = client.get(
        f"/api/v1/kardex/articulos/{articulo.id}/conciliacion-inicial",
        headers=headers)
    assert conciliacion.status_code == 200
    assert conciliacion.json()["estado"] == "NO_DISPONIBLE"


def test_consignacion_retorna_unidades_y_exige_documentos_y_area(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    headers = auth_headers(usuario_admin)
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/custodias-externas"
    datos = entrega(articulo, origen, usuario_admin, tipo="CONSIGNACION",
                    ubicacion_externa="Librería Central")
    assert client.post(ruta, headers=headers, json={**datos,
        "receptor_nombre": "  "}).status_code == 422
    assert client.post(ruta, headers=headers, json={**datos,
        "cantidad": 7}).status_code == 409
    creada = client.post(ruta, headers=headers, json=datos)
    assert creada.status_code == 200, creada.text
    cid = creada.json()["registro"]["id"]
    ruta_eventos = f"{ruta}/{cid}/eventos"
    assert client.post(ruta_eventos, headers=headers,
        json=evento(usuario_admin, tipo="RETORNO")).status_code == 422
    assert client.post(ruta_eventos, headers=headers,
        json=evento(usuario_admin, comprador="  ")).status_code == 422
    retorno = evento(usuario_admin, tipo="RETORNO", area_destino_id=destino.id,
                     cantidad=2)
    respuesta = client.post(ruta_eventos, headers=headers, json=retorno)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["custodia"]["cantidad_fuera"] == 1
    assert respuesta.json()["custodia"]["cantidad_devuelta"] == 2
    assert respuesta.json()["distribucion"]["total_institucional"] == 10
    assert respuesta.json()["distribucion"]["en_custodia_externa"] == 1
    assert client.post(ruta_eventos, headers=headers, json={**retorno,
        "cantidad": 2, "solicitud_id": str(uuid4())}).status_code == 409
    venta = client.post(ruta_eventos, headers=headers, json=evento(usuario_admin))
    assert venta.status_code == 200, venta.text
    final = client.get(ruta, headers=headers).json()[0]
    assert (final["cantidad_entregada"], final["cantidad_fuera"],
            final["cantidad_vendida"], final["cantidad_devuelta"]) == (3, 0, 1, 2)
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 9
    assert {e.area_id: e.cantidad for e in db_session.query(Existencia).filter_by(
        activo_id=articulo.id).all()} == {origen.id: 3, destino.id: 6}
    assert client.get(f"/api/v1/kardex/articulos/{articulo.id}/kardex-digital",
                      headers=headers).json()["integridad"] is True


def test_entrega_y_venta_alertadas_exigen_confirmacion_sin_escribir_antes(
    client, db_session, usuario_admin, activos_prueba, monkeypatch,
):
    monkeypatch.setattr(settings, "CONTROL_CANTIDAD_EXTREMA", 2)
    articulo, _ = activos_prueba
    origen, _ = escenario(client, db_session, usuario_admin, articulo)
    headers = auth_headers(usuario_admin)
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/custodias-externas"
    datos = entrega(articulo, origen, usuario_admin)
    previa = client.post(ruta, headers=headers, json=datos)
    assert previa.status_code == 409
    assert previa.json()["detail"]["codigo"] == "ALERTAS_CONTROL"
    assert db_session.query(CustodiaExterna).count() == 0
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 10
    firma = previa.json()["detail"]["firma_confirmacion"]
    assert client.post(ruta, headers=headers, json={**datos,
        "confirmacion_alertas": firma, "motivo_alertas": "corto"}).status_code == 422
    confirmada = client.post(ruta, headers=headers, json={**datos,
        "confirmacion_alertas": firma,
        "motivo_alertas": "Entrega autorizada por acta"})
    assert confirmada.status_code == 200, confirmada.text
    assert "CANTIDAD_EXTREMA" in {a["codigo"] for a in confirmada.json()["registro"]["alertas_control"]}
    cid = confirmada.json()["registro"]["id"]
    ruta_eventos = f"{ruta}/{cid}/eventos"
    venta = evento(usuario_admin, cantidad=2)
    venta_previa = client.post(ruta_eventos, headers=headers, json=venta)
    assert venta_previa.status_code == 409
    assert venta_previa.json()["detail"]["codigo"] == "ALERTAS_CONTROL"
    assert db_session.query(EventoCustodiaExterna).count() == 0
    venta_confirmada = client.post(ruta_eventos, headers=headers, json={**venta,
        "confirmacion_alertas": venta_previa.json()["detail"]["firma_confirmacion"],
        "motivo_alertas": "Venta comprobada con factura"})
    assert venta_confirmada.status_code == 200, venta_confirmada.text
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 8
    assert db_session.query(EventoCustodiaExterna).count() == 1
