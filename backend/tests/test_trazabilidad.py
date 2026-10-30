"""Trazabilidad legible sin convertir deducciones del OCR en rutas físicas."""
from datetime import UTC, date, datetime
from uuid import uuid4

from app.models.inventario import AperturaInventario
from app.models.kardex import LoteCarga, MovimientoKardex
from test_kardex import activos_prueba, auth_headers, crear_movimiento, usuario_auditor
from test_transferencias_area import escenario, datos
from test_ajustes_operativos import prueba_movimiento, rectificacion
from test_custodias_externas import entrega, evento


def consulta(client, usuario, articulo, **params):
    r = client.get(f"/api/v1/kardex/articulos/{articulo.id}/trazabilidad",
                   headers=auth_headers(usuario), params=params)
    assert r.status_code == 200, r.text
    d = r.json()
    ids = {n["id"] for n in d["nodes"]}
    assert len(ids) == len(d["nodes"])
    assert all(l["source"] in ids and l["target"] in ids for l in d["links"])
    return d


def test_historico_muestra_evidencia_y_no_inventa_almacen_ni_responsable(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    lote = LoteCarga(total_imagenes=1, tanda=2)
    db_session.add(lote); db_session.commit()
    m = crear_movimiento(db_session, articulo_id=articulo.id, lote_id=lote.id,
        fecha=date(2025, 12, 31), saldo=8, ingresos=8, numero_pagina=1, orden_fila=3)
    m.ruta_imagen_respaldo = "storage\\kardex\\hoja uno.png"
    m.nodo_grafo = "Área: Galería"; m.area_estado = "RESUELTA_AUTOMATICAMENTE"
    db_session.commit()
    d = consulta(client, usuario_admin, articulo, ambito="HISTORICO", tanda=2)
    e = d["eventos"][0]
    assert (d["total"], d["pendientes"]) == (1, 1)
    assert (e["tanda"], e["pagina"], e["fila"]) == (2, 1, 3)
    assert e["imagen_url"] == "/storage/kardex/hoja%20uno.png"
    assert e["encargado"] is None and e["receptor"] is None
    assert not e["afecta_stock_actual"]
    assert all(n["label"] != "Almacén Central" for n in d["nodes"])
    assert all(l["certeza"] == "PENDIENTE" for l in d["links"])
    assert db_session.get(AperturaInventario, articulo.id) is None
    m.area_estado = "RESUELTA_POR_HUMANO"; db_session.commit()
    revisado = consulta(client, usuario_admin, articulo)
    assert {l["certeza"] for l in revisado["links"]} == {"CONFIRMADA", "PENDIENTE"}
    assert consulta(client, usuario_admin, articulo, tanda=1)["total"] == 0


def test_historico_distingue_asignacion_inferida_de_referencia_confirmada(client,db_session,usuario_admin,activos_prueba):
    articulo,_=activos_prueba
    lote=LoteCarga(total_imagenes=1);db_session.add(lote);db_session.flush()
    m=crear_movimiento(db_session,articulo_id=articulo.id,lote_id=lote.id,fecha=date(2020,1,1),saldo=2,ingresos=2,numero_pagina=1,orden_fila=1)
    m.area='CDP';m.nodo_grafo='Área: Capacitación';m.area_estado='PENDIENTE_HIL';m.requiere_auditoria_nodo=True
    m.revision_documental={'asignacion_area':{'estado':'INFERIDA','area':'Capacitación','motivo':'Correlación; identidad no confirmada'}}
    db_session.commit()
    d=consulta(client,usuario_admin,articulo)
    e=d['eventos'][0]
    assert e['area_documental']=='CDP' and e['asignacion_area']['area']=='Capacitación'
    assert e['estado_relacion']=='PENDIENTE'
    assert any(c['etiqueta']=='Área inferida por correlación' for c in e['conexiones'])


def test_transferencias_devoluciones_rectificaciones_y_contexto_fuera_de_fecha(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    headers = auth_headers(usuario_admin)
    traslado = client.post(f"/api/v1/kardex/articulos/{articulo.id}/transferencias",
        headers=headers, json=datos(origen, destino, usuario_admin))
    assert traslado.status_code == 200
    venta = prueba_movimiento(client, usuario_admin, articulo, destino, cantidad=2)
    devolucion = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
        json={"solicitud_id": str(uuid4()), "articulo_id": articulo.id, "tipo": "ingreso",
              "cantidad": 1, "nodo_grafo": "Devolución", "tipo_operacion": "Devolución",
              "movimiento_origen_id": venta["id"], "devuelto_por": "Biblioteca",
              "area_operativa_id": origen.id, "referencia_documento": "ACTA-DEV-01"})
    assert devolucion.status_code == 200, devolucion.text
    correccion = client.post(f"/api/v1/kardex/movimiento-actual/{venta['id']}/corregir",
        headers=headers, json=rectificacion(1))
    assert correccion.status_code == 200, correccion.text
    v = db_session.get(MovimientoKardex, venta["id"])
    v.ocurrido_en = datetime(2026, 10, 8, 2, tzinfo=UTC)  # 7 de octubre en Bolivia
    db_session.get(MovimientoKardex, devolucion.json()["id"]).ocurrido_en = datetime(2026, 10, 8, 5, tzinfo=UTC)
    db_session.get(MovimientoKardex, correccion.json()["id"]).ocurrido_en = datetime(2026, 10, 8, 6, tzinfo=UTC)
    db_session.commit()
    todo = consulta(client, usuario_admin, articulo)
    t = next(e for e in todo["eventos"] if e["clase"] == "TRANSFERENCIA")
    assert [c["ubicacion"] for c in t["conexiones"]] == [f"area:{origen.id}", f"area:{destino.id}"]
    assert not t["afecta_stock_actual"]
    assert {e["clase"] for e in todo["eventos"]} >= {"UBICACION", "BASE", "OPERACION", "TRANSFERENCIA"}
    assert todo["integridad_libro"] is True and todo["saldo_actual"] == 10
    por_area = consulta(client, usuario_admin, articulo, ubicacion=f"area:{origen.id}")
    assert all(any(c["ubicacion"] == f"area:{origen.id}" for c in e["conexiones"]) for e in por_area["eventos"])
    d = consulta(client, usuario_admin, articulo, desde="2026-10-08", hasta="2026-10-08")
    assert {e["clave"] for e in d["contexto"]} == {f"OPERACION:{venta['id']}"}
    assert {l["label"] for l in d["links"] if l["tipo"] == "VINCULO"} == {"RECTIFICA", "DEVUELVE"}
    assert all(e["id"] != venta["id"] for e in d["eventos"] if e["clase"] == "OPERACION")
    assert db_session.get(MovimientoKardex, venta["id"]).salidas == 2
    # Aun mostrando únicamente la rectificación de una recepción, se conserva
    # la recepción y la venta a la que ésta corresponde, ambas fuera de página.
    ajuste_devolucion = client.post(f"/api/v1/kardex/movimiento-actual/{devolucion.json()['id']}/corregir",
        headers=headers, json=rectificacion(0))
    assert ajuste_devolucion.status_code == 200
    todos = consulta(client, usuario_admin, articulo)
    indice = next(i for i, e in enumerate(todos["eventos"]) if e["clave"] == f"OPERACION:{ajuste_devolucion.json()['id']}")
    uno = consulta(client, usuario_admin, articulo, limite=1, offset=indice)
    assert {e["clave"] for e in uno["contexto"]} == {f"OPERACION:{venta['id']}", f"OPERACION:{devolucion.json()['id']}"}
    assert {l["label"] for l in uno["links"] if l["tipo"] == "VINCULO"} == {"RECTIFICA", "DEVUELVE"}


def test_custodia_identifica_entrega_origen_venta_y_retorno(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/custodias-externas"
    headers = auth_headers(usuario_admin)
    c = client.post(ruta, headers=headers, json=entrega(articulo, origen, usuario_admin))
    assert c.status_code == 200
    cid = c.json()["registro"]["id"]
    for payload in (evento(usuario_admin), evento(usuario_admin, tipo="RETORNO", area_destino_id=destino.id)):
        assert client.post(f"{ruta}/{cid}/eventos", headers=headers, json=payload).status_code == 200
    d = consulta(client, usuario_admin, articulo, ubicacion=f"custodia:{cid}")
    assert d["total"] == 3 and d["saldo_actual"] == 9
    assert {e["clase"] for e in d["eventos"]} == {"CUSTODIA_ENTREGA", "CUSTODIA_VENTA", "CUSTODIA_RETORNO"}
    assert len([l for l in d["links"] if l["label"] == "RESULTADO_CUSTODIA"]) == 2
    retorno = next(e for e in d["eventos"] if e["clase"] == "CUSTODIA_RETORNO")
    assert retorno["conexiones"][1]["ubicacion"] == f"area:{destino.id}"
    assert not retorno["afecta_stock_actual"]


def test_base_enlaza_cierre_fijado_aunque_haya_nuevos_escaneos_y_paginacion(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    escenario(client, db_session, usuario_admin, articulo)
    lote = LoteCarga(total_imagenes=1, tanda=1)
    db_session.add(lote); db_session.commit()
    cierre = crear_movimiento(db_session, articulo_id=articulo.id, lote_id=lote.id,
        fecha=date(2025, 12, 30), saldo=10, ingresos=10)
    apertura = db_session.get(AperturaInventario, articulo.id)
    apertura.origen = "KARDEX_HISTORICO"; apertura.movimiento_historico_id = cierre.id
    apertura.lote_historico_id = lote.id; db_session.commit()
    crear_movimiento(db_session, articulo_id=articulo.id, lote_id=lote.id,
        fecha=date(2025, 12, 31), saldo=14, ingresos=4)
    d = consulta(client, usuario_admin, articulo, ambito="OPERATIVO")
    b = next(e for e in d["eventos"] if e["clase"] == "BASE")
    assert b["cantidad"] == 10 and b["vinculos"] == [{"destino": f"HISTORICO:{cierre.id}", "tipo": "BASE_HISTORICA"}]
    assert d["contexto"][0]["id"] == cierre.id
    assert d["saldo_actual"] == 10
    a = consulta(client, usuario_admin, articulo, limite=1)
    siguiente = consulta(client, usuario_admin, articulo, limite=1, offset=1)
    assert a["total"] == siguiente["total"] == 5
    assert a["eventos"][0]["clave"] != siguiente["eventos"][0]["clave"]


def test_validacion_autenticacion_y_antecedentes_no_operativos(
    client, db_session, usuario_admin, usuario_auditor, activos_prueba,
):
    articulo, _ = activos_prueba
    viejo = crear_movimiento(db_session, articulo_id=articulo.id, fecha=date(2025, 1, 1), ingresos=99, saldo=99)
    viejo.ruta_imagen_respaldo = "storage/../privado.txt"; db_session.commit()
    d = consulta(client, usuario_auditor, articulo)
    assert d["eventos"][0]["clase"] == "ANTECEDENTE"
    assert d["eventos"][0]["imagen_url"] is None
    assert d["saldo_actual"] is None
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/trazabilidad"
    assert client.get(ruta).status_code == 401
    for params in ({"desde": "2026-10-09", "hasta": "2026-10-08"}, {"limite": 101}, {"offset": -1}, {"ambito": "INVALIDO"}):
        assert client.get(ruta, headers=auth_headers(usuario_admin), params=params).status_code == 422
    assert client.get("/api/v1/kardex/articulos/999999/trazabilidad", headers=auth_headers(usuario_admin)).status_code == 404
