from datetime import UTC, datetime
from uuid import uuid4
import csv
import io
import pytest
from app.models.activos import Existencia
from app.models.auditoria import AuditoriaSistema
from app.models.inventario import AperturaInventario, CustodiaExterna, EventoCustodiaExterna, TransferenciaArea
from app.models.rectificacion_logistica import RectificacionLogistica
from app.services.rectificaciones_logisticas import estado_vigente
from test_kardex import activos_prueba, auth_headers, usuario_auditor
from test_transferencias_area import escenario
from test_custodias_externas import entrega, evento


@pytest.fixture
def logistica(client, db_session, usuario_admin, activos_prueba):
    articulo = activos_prueba[0]
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    return articulo, origen, destino


def corregir(client, usuario, articulo, registro, clase, **cambios):
    datos = {**registro["datos_vigentes"], "clase": clase, **cambios}
    payload = dict(solicitud_id=str(uuid4()), registro_id=registro["id"], cambios=datos,
        version_esperada=registro["version_rectificacion"], referencia_documento="ACTA-CORR-QA",
        motivo="Se cotejó el comprobante y se corrige el error de registro.", evidencia_revisada=True)
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/rectificaciones-logisticas"
    return client.post(ruta, headers=auth_headers(usuario), json=payload), payload


def nueva_transferencia(client, articulo, origen, destino, usuario):
    return client.post(f"/api/v1/kardex/articulos/{articulo.id}/transferencias",
        headers=auth_headers(usuario), json=dict(solicitud_id=str(uuid4()), area_origen_id=origen.id,
        area_destino_id=destino.id, cantidad=2, encargado_id=usuario.id,
        referencia_documento="ACTA-T-QA")).json()["registro"]


def custodiar(client, articulo, origen, usuario):
    r = client.post(f"/api/v1/kardex/articulos/{articulo.id}/custodias-externas",
                    headers=auth_headers(usuario), json=entrega(articulo, origen, usuario))
    assert r.status_code == 200, r.text
    return r.json()["registro"]


def leer_custodia(client, articulo, usuario):
    return client.get(f"/api/v1/kardex/articulos/{articulo.id}/custodias-externas",
                      headers=auth_headers(usuario)).json()[0]


def cantidades(db, articulo):
    return {e.area_id: int(e.cantidad) for e in db.query(Existencia).filter_by(activo_id=articulo.id)}


def test_transferencia_variar_cantidad_areas_anular_reintentar_y_trazar(client, db_session, logistica, usuario_admin):
    a, origen, destino = logistica
    t = nueva_transferencia(client, a, origen, destino, usuario_admin)
    r, payload = corregir(client, usuario_admin, a, t, "TRANSFERENCIA", cantidad=1)
    assert r.status_code == 200, r.text
    ruta = f"/api/v1/kardex/articulos/{a.id}/rectificaciones-logisticas"
    assert client.post(ruta, headers=auth_headers(usuario_admin), json=payload).json()["registro"]["id"] == r.json()["registro"]["id"]
    assert cantidades(db_session, a) == {origen.id: 5, destino.id: 5}
    actual = client.get(f"/api/v1/kardex/articulos/{a.id}/transferencias", headers=auth_headers(usuario_admin)).json()[0]
    r2, _ = corregir(client, usuario_admin, a, actual, "TRANSFERENCIA", area_origen_id=destino.id, area_destino_id=origen.id, cantidad=2)
    assert r2.status_code == 200, r2.text
    assert r2.json()["registro"]["anterior_id"] == r.json()["registro"]["id"]
    assert cantidades(db_session, a) == {origen.id: 8, destino.id: 2}
    actual = client.get(f"/api/v1/kardex/articulos/{a.id}/transferencias", headers=auth_headers(usuario_admin)).json()[0]
    r3, _ = corregir(client, usuario_admin, a, actual, "TRANSFERENCIA", cantidad=0)
    assert r3.status_code == 200
    assert cantidades(db_session, a) == {origen.id: 6, destino.id: 4}
    original = db_session.get(TransferenciaArea, t["id"])
    assert original.cantidad == 2 and original.area_origen_id == origen.id
    assert db_session.get(AperturaInventario, a.id).cantidad_actual == 10
    assert db_session.query(RectificacionLogistica).count() == 3
    assert db_session.query(AuditoriaSistema).filter_by(accion="rectificar_logistica").count() == 3
    h = auth_headers(usuario_admin)
    libro = client.get(f"/api/v1/kardex/articulos/{a.id}/kardex-digital", headers=h).json()
    assert libro["integridad"] and libro["saldo_final"] == 10
    assert len(libro["eventos"]) == 4
    grafo = client.get(f"/api/v1/kardex/articulos/{a.id}/trazabilidad?ambito=OPERATIVO&limite=100", headers=h).json()
    assert any(l["label"] == "RECTIFICA" for l in grafo["links"])
    csvr = client.get(f"/api/v1/kardex/articulos/{a.id}/kardex-digital.csv", headers=h)
    filas = list(csv.DictReader(io.StringIO(csvr.text.lstrip("\ufeff")), delimiter=";"))
    assert filas[-1]["corrige_clase"] == "TRANSFERENCIA" and filas[-1]["cantidad_corregida"] == "0"


def test_entrega_corregida_con_ventas_posteriores_y_contexto(client, db_session, logistica, usuario_admin):
    a, origen, destino = logistica
    c = custodiar(client, a, origen, usuario_admin)
    r, _ = corregir(client, usuario_admin, a, c, "ENTREGA", cantidad=4)
    assert r.status_code == 200, r.text
    assert cantidades(db_session, a)[origen.id] == 2
    cust = db_session.get(CustodiaExterna, c["id"])
    assert cust.cantidad_entregada == 3 and cust.cantidad_ajustada == 1 and cust.cantidad_fuera == 4
    evt = client.post(f"/api/v1/kardex/articulos/{a.id}/custodias-externas/{c['id']}/eventos",
        headers=auth_headers(usuario_admin), json=evento(usuario_admin, cantidad=2))
    assert evt.status_code == 200, evt.text
    actual = leer_custodia(client, a, usuario_admin)
    assert corregir(client, usuario_admin, a, actual, "ENTREGA", cantidad=1)[0].status_code == 409
    r, _ = corregir(client, usuario_admin, a, actual, "ENTREGA", receptor_nombre="Nuevo receptor cotejado",
                    ubicacion_externa="Puesto corregido", referencia_documento="ACTA-ENTREGA-COTEJADA")
    assert r.status_code == 200, r.text
    actual = leer_custodia(client, a, usuario_admin)
    assert actual["receptor_nombre"] == "Nuevo receptor cotejado"
    assert actual["cantidad_entregada"] == 4 and actual["cantidad_fuera"] == 2 and actual["cantidad_vendida"] == 2
    assert cust.receptor_nombre == "Centro Cultural"
    assert cust.cantidad_entregada + cust.cantidad_ajustada == cust.cantidad_fuera + cust.cantidad_vendida + cust.cantidad_devuelta


def test_venta_rectificada_a_retorno_y_anulada_con_balance(client, db_session, logistica, usuario_admin):
    a, origen, destino = logistica
    c = custodiar(client, a, origen, usuario_admin)
    ruta = f"/api/v1/kardex/articulos/{a.id}/custodias-externas/{c['id']}/eventos"
    e = client.post(ruta, headers=auth_headers(usuario_admin), json=evento(usuario_admin)).json()["registro"]
    r, _ = corregir(client, usuario_admin, a, e, "EVENTO_CUSTODIA", cantidad=2)
    assert r.status_code == 200, r.text
    actual = leer_custodia(client, a, usuario_admin)["eventos"][0]
    r2, _ = corregir(client, usuario_admin, a, actual, "EVENTO_CUSTODIA", tipo="RETORNO",
                      area_destino_id=destino.id, comprador=None)
    assert r2.status_code == 200, r2.text
    assert cantidades(db_session, a) == {origen.id: 3, destino.id: 6}
    apertura = db_session.get(AperturaInventario, a.id)
    assert apertura.cantidad_actual == 10 and apertura.cantidad_custodia_externa == 1
    actual = leer_custodia(client, a, usuario_admin)["eventos"][0]
    assert corregir(client, usuario_admin, a, actual, "EVENTO_CUSTODIA", cantidad=0)[0].status_code == 200
    assert cantidades(db_session, a) == {origen.id: 3, destino.id: 4}
    assert apertura.cantidad_actual == 10 and apertura.cantidad_custodia_externa == 3
    original = db_session.get(EventoCustodiaExterna, e["id"])
    assert original.tipo == "VENTA" and original.cantidad == 1 and original.area_destino_id is None
    libro = client.get(f"/api/v1/kardex/articulos/{a.id}/kardex-digital", headers=auth_headers(usuario_admin)).json()
    assert libro["integridad"] and libro["saldo_final"] == 10
    informe = client.get("/api/v1/reportes/institucional?gestion=2026", headers=auth_headers(usuario_admin)).json()
    assert informe["articulos_con_error_integridad"] == []
    assert informe["resumen_periodo"]["rectificaciones_logisticas"] == 3


def test_compensacion_imposible_por_consumo_posterior_no_deja_asientos(client, db_session, logistica, usuario_admin):
    a, origen, destino = logistica
    c = custodiar(client, a, origen, usuario_admin)
    e = client.post(f"/api/v1/kardex/articulos/{a.id}/custodias-externas/{c['id']}/eventos",
        headers=auth_headers(usuario_admin), json=evento(usuario_admin, tipo="RETORNO", area_destino_id=destino.id)).json()["registro"]
    # Estado equivalente a vender luego todas las unidades recibidas en ese área.
    ex = db_session.query(Existencia).filter_by(activo_id=a.id, area_id=destino.id).one()
    apertura = db_session.get(AperturaInventario, a.id)
    apertura.cantidad_actual -= int(ex.cantidad); ex.cantidad = 0
    db_session.commit()
    antes = apertura.cantidad_actual
    assert corregir(client, usuario_admin, a, e, "EVENTO_CUSTODIA", cantidad=0)[0].status_code == 409
    assert db_session.query(RectificacionLogistica).count() == 0
    assert db_session.get(AperturaInventario, a.id).cantidad_actual == antes


def test_no_se_usa_version_anterior_ni_solicitud_para_otro_contenido(client, db_session, logistica, usuario_admin):
    a, origen, destino = logistica
    t = nueva_transferencia(client, a, origen, destino, usuario_admin)
    r, payload = corregir(client, usuario_admin, a, t, "TRANSFERENCIA", cantidad=1)
    assert r.status_code == 200
    assert corregir(client, usuario_admin, a, t, "TRANSFERENCIA", cantidad=0)[0].status_code == 409
    payload["motivo"] = "Otro contenido con la misma clave de solicitud."
    assert client.post(f"/api/v1/kardex/articulos/{a.id}/rectificaciones-logisticas",
        headers=auth_headers(usuario_admin), json=payload).status_code == 409
    assert db_session.query(RectificacionLogistica).count() == 1


@pytest.mark.parametrize("rol", ["operador", "auditor"])
def test_roles_y_api_directa(client, db_session, logistica, usuario_admin, usuario_operador, usuario_auditor, rol):
    a, origen, destino = logistica
    t = nueva_transferencia(client, a, origen, destino, usuario_admin)
    u = usuario_operador if rol == "operador" else usuario_auditor
    r, _ = corregir(client, u, a, t, "TRANSFERENCIA", cantidad=1)
    assert r.status_code == 403
    assert db_session.query(RectificacionLogistica).count() == 0


def test_cierre_anual_reconstruye_antes_de_la_compensacion(client, db_session, logistica, usuario_admin, monkeypatch):
    a, origen, destino = logistica
    t = nueva_transferencia(client, a, origen, destino, usuario_admin)
    apertura = db_session.get(AperturaInventario, a.id)
    apertura.aprobado_en = datetime(2025, 1, 1, tzinfo=UTC)
    tr = db_session.get(TransferenciaArea, t["id"])
    tr.registrado_en = tr.ocurrido_en = datetime(2025, 12, 20, tzinfo=UTC)
    for audit in db_session.query(AuditoriaSistema).filter_by(accion="asignar_existencia_area"):
        audit.fecha_hora = datetime(2025, 1, 2, tzinfo=UTC)
    db_session.commit()
    assert corregir(client, usuario_admin, a, t, "TRANSFERENCIA", cantidad=0)[0].status_code == 200
    from app.services.cierre_anual import reconstruir
    reconstruido = reconstruir(db_session, 2025)
    snap = reconstruido["snapshot"]
    assert not reconstruido["impedimentos"]
    fila = next(f for f in snap["articulos"] if f["articulo_id"] == a.id)
    assert fila["total"] == 10
    assert {int(f["area_id"]): f["cantidad"] for f in fila["areas"]} == {origen.id: 4, destino.id: 6}


def test_correccion_venta_posterior_conserva_huella_balance_anterior(client, db_session, logistica, usuario_admin):
    a, origen, destino = logistica
    c = custodiar(client, a, origen, usuario_admin)
    e = client.post(f"/api/v1/kardex/articulos/{a.id}/custodias-externas/{c['id']}/eventos",
        headers=auth_headers(usuario_admin), json=evento(usuario_admin)).json()["registro"]
    apertura = db_session.get(AperturaInventario, a.id)
    apertura.aprobado_en = datetime(2025, 1, 1, tzinfo=UTC)
    cust = db_session.get(CustodiaExterna, c["id"])
    cust.ocurrido_en = cust.registrado_en = datetime(2025, 12, 20, tzinfo=UTC)
    venta = db_session.get(EventoCustodiaExterna, e["id"])
    venta.ocurrido_en = venta.registrado_en = datetime(2025, 12, 21, tzinfo=UTC)
    for audit in db_session.query(AuditoriaSistema).filter_by(accion="asignar_existencia_area"):
        audit.fecha_hora = datetime(2025, 1, 2, tzinfo=UTC)
    db_session.commit()
    from app.services.cierre_anual import reconstruir
    antes = reconstruir(db_session, 2025)
    assert not antes["impedimentos"]
    assert corregir(client, usuario_admin, a, e, "EVENTO_CUSTODIA", cantidad=0)[0].status_code == 200
    despues = reconstruir(db_session, 2025)
    assert not despues["impedimentos"] and despues["huella"] == antes["huella"]
    fila = next(f for f in despues["snapshot"]["articulos"] if f["articulo_id"] == a.id)
    assert fila["total"] == 9 and fila["custodia"] == 2
