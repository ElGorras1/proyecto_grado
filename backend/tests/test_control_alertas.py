"""Seguimiento, permisos, concurrencia y preservación del stock."""
from datetime import UTC, datetime
from uuid import uuid4
import pytest
from app.models.auditoria import AuditoriaSistema
from app.models.control_alertas import CasoControl, RevisionControl
from app.models.inventario import AperturaInventario, CustodiaExterna
from app.models.kardex import MovimientoKardex
from app.services.control_alertas import incorporar_avisos_guardados, registrar_caso
from test_kardex import activos_prueba, auth_headers, usuario_auditor
from test_transferencias_area import escenario, datos, cantidades
from test_custodias_externas import entrega, evento

RUTA = "/api/v1/control-alertas"

def alertada(client, usuario, articulo, origen):
    payload = {"solicitud_id": str(uuid4()), "articulo_id": articulo.id, "tipo": "salida",
        "cantidad": 6, "tipo_operacion": "Ventas", "nodo_grafo": "Ventas",
        "area_operativa_id": origen.id, "receptor": "Biblioteca", "receptor_tipo": "INSTITUCION",
        "referencia_documento": "FACT-ALERTA"}
    ruta = "/api/v1/kardex/movimiento-actual"
    d = client.post(ruta, headers=auth_headers(usuario), json=payload).json()["detail"]
    payload.update(confirmacion_alertas=d["firma_confirmacion"], motivo_alertas="Venta completa del área aprobada mediante acta")
    r = client.post(ruta, headers=auth_headers(usuario), json=payload)
    assert r.status_code == 200, r.text
    return r.json(), payload

def decision(client, usuario, caso_id, **cambios):
    actual = client.get(f"{RUTA}/{caso_id}", headers=auth_headers(usuario)).json()
    return dict(solicitud_id=str(uuid4()), revision_esperada=actual["revision_numero"],
        huella_contexto=actual["huella_contexto"], estado="EN_REVISION", prioridad="ALTA",
        asignado_id=usuario.id, conclusion="NO_CONCLUYENTE",
        motivo="Inicio de revisión del acta de salida y ubicación", documento=None,
        correccion_movimiento_id=None) | cambios

@pytest.mark.parametrize("clase", ["MOVIMIENTO", "TRANSFERENCIA", "CUSTODIA", "EVENTO_CUSTODIA"])
def test_un_caso_por_operacion_confirmada_y_nunca_por_vista_previa(
    clase, client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    headers = auth_headers(usuario_admin)
    if clase == "MOVIMIENTO":
        payload = {"solicitud_id": str(uuid4()), "articulo_id": articulo.id, "tipo": "salida", "cantidad": 6,
            "tipo_operacion": "Ventas", "nodo_grafo": "Ventas", "area_operativa_id": origen.id,
            "receptor": "Biblioteca", "receptor_tipo": "INSTITUCION", "referencia_documento": "FACT-ALERTA"}
        ruta = "/api/v1/kardex/movimiento-actual"
    elif clase == "TRANSFERENCIA":
        payload = datos(origen, destino, usuario_admin, cantidad=6)
        ruta = f"/api/v1/kardex/articulos/{articulo.id}/transferencias"
    else:
        ruta = f"/api/v1/kardex/articulos/{articulo.id}/custodias-externas"
        payload = entrega(articulo, origen, usuario_admin)
        if clase == "CUSTODIA":
            payload["cantidad"] = 6
        else:
            c = client.post(ruta, headers=headers, json=payload).json()["registro"]["id"]
            ruta += f"/{c}/eventos"
            payload = evento(usuario_admin, tipo="RETORNO", area_destino_id=destino.id)
            assert client.post(ruta, headers=headers, json=payload).status_code == 200
            payload["solicitud_id"] = str(uuid4())
    antes = cantidades(db_session, articulo.id)
    previa = client.post(ruta, headers=headers, json=payload)
    assert previa.status_code == 409, previa.text
    assert db_session.query(CasoControl).count() == 0
    assert cantidades(db_session, articulo.id) == antes
    detalle = previa.json()["detail"]
    payload.update(confirmacion_alertas=detalle["firma_confirmacion"], motivo_alertas="Operación documental revisada y autorizada")
    final = client.post(ruta, headers=headers, json=payload)
    assert final.status_code == 200, final.text
    assert client.post(ruta, headers=headers, json=payload).status_code == 200
    c = db_session.query(CasoControl).one()
    assert c.snapshot["clase"] == clase and c.estado == "PENDIENTE"
    assert c.asignado_id is None and c.revision_numero == 0
    assert c.snapshot["justificacion_operador"] == payload["motivo_alertas"]
    assert incorporar_avisos_guardados(db_session) == 0
    assert db_session.query(CasoControl).count() == 1

def test_revision_cierre_reapertura_auditoria_y_reintento_no_modifican_stock(
    client, db_session, usuario_admin, usuario_auditor, usuario_operador, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, _ = escenario(client, db_session, usuario_admin, articulo)
    movimiento, solicitud = alertada(client, usuario_admin, articulo, origen)
    c = db_session.query(CasoControl).one()
    ruta = f"{RUTA}/{c.id}/revision"
    antes = cantidades(db_session, articulo.id)
    snapshot = dict(c.snapshot)
    p = decision(client, usuario_admin, c.id, asignado_id=usuario_auditor.id)
    assert client.post(ruta, json=p).status_code == 401
    assert client.post(ruta, headers=auth_headers(usuario_operador), json=p).status_code == 403
    assert client.get(RUTA, headers=auth_headers(usuario_operador)).json()["total"] == 1
    inicio = client.post(ruta, headers=auth_headers(usuario_admin), json=p)
    assert inicio.status_code == 200 and inicio.json()["asignado_nombre"] == usuario_auditor.nombre
    assert client.post(ruta, headers=auth_headers(usuario_admin), json=p).json()["reintento"] is True
    assert db_session.query(RevisionControl).count() == 1
    assert client.post(ruta, headers=auth_headers(usuario_admin), json=p | {"motivo": "Mismo UUID con otra decisión"}).status_code == 409
    assert client.post(ruta, headers=auth_headers(usuario_auditor), json=p | {"solicitud_id": str(uuid4())}).status_code == 409
    cerrar = decision(client, usuario_auditor, c.id, estado="JUSTIFICADO", conclusion="LEGITIMO",
        documento="ACTA-VERIFICACION", motivo="Comprobado el pedido y el acta de salida completa")
    assert client.post(ruta, headers=auth_headers(usuario_auditor), json=cerrar).status_code == 200
    assert client.get(RUTA, headers=auth_headers(usuario_admin)).json()["total"] == 0
    assert client.get(RUTA + "?estado=TODOS", headers=auth_headers(usuario_admin)).json()["total"] == 1
    reabrir = decision(client, usuario_auditor, c.id, motivo="Nueva evidencia documental requiere revisión adicional")
    assert client.post(ruta, headers=auth_headers(usuario_auditor), json=reabrir).status_code == 200
    assert db_session.query(RevisionControl).count() == 3
    assert db_session.query(AuditoriaSistema).filter_by(accion="revisar_alerta_operativa").count() == 3
    assert cantidades(db_session, articulo.id) == antes
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 4
    assert db_session.get(MovimientoKardex, movimiento["id"]).salidas == 6
    db_session.refresh(c)
    assert c.snapshot == snapshot
    h = client.get(f"{RUTA}/{c.id}/revisiones?limite=2", headers=auth_headers(usuario_admin)).json()
    assert h["total"] == 3 and len(h["filas"]) == 2
    assert h["filas"][0]["usuario_nombre"] == usuario_auditor.nombre

def test_no_cierra_sin_evidencia_o_con_correccion_pendiente_ni_asigna_operador(
    client, db_session, usuario_admin, usuario_operador, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, _ = escenario(client, db_session, usuario_admin, articulo)
    alertada(client, usuario_admin, articulo, origen)
    c = db_session.query(CasoControl).one(); ruta = f"{RUTA}/{c.id}/revision"; headers = auth_headers(usuario_admin)
    assert client.post(ruta, headers=headers, json=decision(client, usuario_admin, c.id, estado="CERRADO", conclusion="LEGITIMO", documento="ACTA")).status_code == 422
    assert client.post(ruta, headers=headers, json=decision(client, usuario_admin, c.id, asignado_id=usuario_operador.id)).status_code == 422
    assert client.post(ruta, headers=headers, json=decision(client, usuario_admin, c.id, motivo=" " * 12)).status_code == 422
    assert client.post(ruta, headers=headers, json=decision(client, usuario_admin, c.id)).status_code == 200
    for cambio in (
        dict(estado="CERRADO", conclusion="NO_CONCLUYENTE", documento="ACTA"),
        dict(estado="CERRADO", conclusion="REQUIERE_CORRECCION", documento="ACTA"),
        dict(estado="JUSTIFICADO", conclusion="LEGITIMO", documento=None),
        dict(estado="JUSTIFICADO", conclusion="CORREGIDO", documento="ACTA"),
        dict(estado="CERRADO", conclusion="CORREGIDO", documento="ACTA", correccion_movimiento_id=999),
    ):
        assert client.post(ruta, headers=headers, json=decision(client, usuario_admin, c.id, **cambio)).status_code == 422
    assert db_session.query(RevisionControl).count() == 1

def test_cambio_de_cantidad_exige_releer_y_cierre_vincula_rectificacion_real(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, _ = escenario(client, db_session, usuario_admin, articulo)
    m, _ = alertada(client, usuario_admin, articulo, origen)
    c = db_session.query(CasoControl).one(); ruta = f"{RUTA}/{c.id}/revision"; headers = auth_headers(usuario_admin)
    assert client.post(ruta, headers=headers, json=decision(client, usuario_admin, c.id)).status_code == 200
    antigua = decision(client, usuario_admin, c.id)
    r = client.post(f"/api/v1/kardex/movimiento-actual/{m['id']}/corregir", headers=headers,
        json={"solicitud_id": str(uuid4()), "cantidad_corregida": 5, "motivo": "Cantidad física corregida con respaldo verificado", "referencia_documento": "ACTA-CORRECCION"})
    assert r.status_code == 200, r.text
    assert client.post(ruta, headers=headers, json=antigua).status_code == 409
    final = client.post(ruta, headers=headers, json=decision(client, usuario_admin, c.id,
        estado="CERRADO", conclusion="CORREGIDO", documento="ACTA-CORRECCION",
        correccion_movimiento_id=r.json()["id"]))
    assert final.status_code == 200, final.text
    assert final.json()["operacion"]["cantidad"] == 6 and final.json()["actual"]["cantidad_vigente"] == 5
    assert cantidades(db_session, articulo.id)[origen.id] == 1

def test_cambio_en_custodia_invalida_contexto_de_revision(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    headers = auth_headers(usuario_admin); ruta = f"/api/v1/kardex/articulos/{articulo.id}/custodias-externas"
    p = entrega(articulo, origen, usuario_admin) | {"cantidad": 6}
    d = client.post(ruta, headers=headers, json=p).json()["detail"]
    p.update(confirmacion_alertas=d["firma_confirmacion"], motivo_alertas="Entrega completa para la feria con acta verificada")
    custodia = client.post(ruta, headers=headers, json=p).json()["registro"]["id"]
    c = db_session.query(CasoControl).one()
    antigua = decision(client, usuario_admin, c.id)
    assert client.post(f"{ruta}/{custodia}/eventos", headers=headers,
        json=evento(usuario_admin, tipo="RETORNO", area_destino_id=destino.id)).status_code == 200
    assert client.post(f"{RUTA}/{c.id}/revision", headers=headers, json=antigua).status_code == 409
    assert db_session.query(RevisionControl).count() == 0

def test_filtros_por_fecha_boliviana_codigo_articulo_y_prioridad_son_acotados(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, otro = activos_prueba
    origen, _ = escenario(client, db_session, usuario_admin, articulo)
    alertada(client, usuario_admin, articulo, origen)
    c = db_session.query(CasoControl).one(); headers = auth_headers(usuario_admin)
    c.creado_en = datetime(2026, 10, 8, 3, 59, tzinfo=UTC); db_session.commit()
    assert client.get(RUTA + "?desde=2026-10-08", headers=headers).json()["total"] == 0
    c.creado_en = datetime(2026, 10, 8, 4, 0, tzinfo=UTC); db_session.commit()
    for filtro in ("desde=2026-10-08&hasta=2026-10-08", "codigo=AGOTA_AREA", f"articulo_id={articulo.id}", "prioridad=ALTA", "sin_asignar=true"):
        r = client.get(RUTA + "?" + filtro, headers=headers)
        assert r.status_code == 200 and r.json()["total"] == 1, r.text
    assert client.get(RUTA + "?codigo=CANTIDAD_EXTREMA", headers=headers).json()["total"] == 0
    assert client.get(RUTA + f"?articulo_id={otro.id}", headers=headers).json()["total"] == 0
    for filtro in ("limite=101", "estado=INVENTADO", "desde=2026-10-09&hasta=2026-10-08", "sin_asignar=true&asignado_id=1"):
        assert client.get(RUTA + "?" + filtro, headers=headers).status_code == 422
    assert client.get(RUTA, headers={}).status_code == 401

def test_importacion_de_avisos_existentes_no_inventa_hallazgos_ni_duplica(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, _ = escenario(client, db_session, usuario_admin, articulo)
    m, _ = alertada(client, usuario_admin, articulo, origen)
    db_session.query(CasoControl).delete(); db_session.commit()
    assert incorporar_avisos_guardados(db_session) == 1
    db_session.commit()
    assert incorporar_avisos_guardados(db_session) == 0
    db_session.commit()
    assert db_session.query(CasoControl).one().movimiento_id == m["id"]
