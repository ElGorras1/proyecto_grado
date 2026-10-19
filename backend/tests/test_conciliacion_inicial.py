from datetime import date, timedelta

from app.models.activos import Existencia
from app.models.area import Area
from app.models.auditoria import AuditoriaSistema
from app.models.inventario import AperturaInventario, ConciliacionInicial
from app.models.kardex import LoteCarga, MovimientoKardex
from test_kardex import activos_prueba, auth_headers, crear_movimiento
from test_ajustes_operativos import rectificacion


def datos(areas, encargado_id, **cambios):
    payload = {"fecha_conteo": "2026-10-07", "areas": areas,
               "encargado_id": encargado_id,
               "referencia_documento": "ACTA-CONTEO-01",
               "justificacion": "Conteo físico total verificado con acta",
               "alcance_total": True, "conteo_verificado": True}
    return {**payload, **cambios}


def test_conciliacion_documental_ajusta_y_distribuye_una_vez(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    galeria = Area(nombre="Galería", estado="activo")
    deposito = Area(nombre="Depósito", estado="activo")
    lote = LoteCarga(total_imagenes=1)
    db_session.add_all([galeria, deposito, lote]); db_session.commit()
    historico = crear_movimiento(
        db_session, articulo_id=articulo.id, lote_id=lote.id,
        fecha=date(2025, 12, 31), saldo=10, ingresos=10,
        numero_pagina=1, orden_fila=1,
    )
    headers = auth_headers(usuario_admin)
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/conciliacion-inicial"
    assert client.get(ruta, headers=headers).json()["estado"] == "DISPONIBLE"
    payload = datos([{"area_id": galeria.id, "cantidad": 6},
                     {"area_id": deposito.id, "cantidad": 2}], usuario_admin.id)
    respuesta = client.post(ruta, headers=headers, json=payload)
    assert respuesta.status_code == 200, respuesta.json()
    registro = respuesta.json()["registro"]
    assert (registro["cantidad_base"], registro["cantidad_fisica"],
            registro["diferencia"]) == (10, 8, -2)
    assert registro["movimiento_historico_id"] == historico.id
    assert registro["ajuste_movimiento_id"] is not None
    assert respuesta.json()["distribucion"]["sin_ubicacion_confirmada"] == 0
    assert db_session.get(AperturaInventario, articulo.id).cantidad_inicial == 10
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 8
    assert db_session.query(Existencia).filter_by(activo_id=articulo.id).count() == 2
    ajuste = db_session.get(MovimientoKardex, registro["ajuste_movimiento_id"])
    assert (ajuste.ingresos, ajuste.salidas, ajuste.saldo_registrado) == (None, 2, 8)
    assert ajuste.lote_id is None and historico.saldo_registrado == 10
    assert client.get(ruta, headers=headers).json()["estado"] == "REGISTRADA"
    catalogo = next(a for a in client.get("/api/v1/kardex/articulos", headers=headers).json()
                    if a["id"] == articulo.id)
    assert catalogo["stock_actual"] == 8
    assert catalogo["corte_operativo"]["estado"] == "CONTEO_FISICO_CONCILIADO"
    assert client.post(ruta, headers=headers, json=payload).status_code == 409
    assert client.post(f"/api/v1/kardex/movimiento-actual/{ajuste.id}/anular",
                       headers=headers).status_code == 410
    assert client.post(f"/api/v1/kardex/movimiento-actual/{ajuste.id}/corregir",
                       headers=headers, json=rectificacion(0)).status_code == 409
    assert db_session.query(AuditoriaSistema).filter_by(
        accion="conciliar_inventario_inicial").count() == 1

    salida = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
                          json={"articulo_id": articulo.id,
                                "solicitud_id": "88888888-8888-4888-8888-888888888888",
                                "tipo": "salida",
                                "cantidad": 1, "nodo_grafo": "Ventas",
                                "area_operativa_id": galeria.id,
                                "referencia_documento": "ACTA-SALIDA-01"})
    assert salida.status_code == 200, salida.json()
    assert salida.json()["saldo_registrado"] == 7
    assert client.post(f"/api/v1/kardex/movimiento-actual/{salida.json()['id']}/corregir",
                       headers=headers, json=rectificacion(0)).status_code == 200
    distribucion = client.get(f"/api/v1/kardex/articulos/{articulo.id}/existencias-area",
                              headers=headers).json()
    assert distribucion["total_institucional"] == 8
    assert {x["area"]: x["cantidad"] for x in distribucion["areas"]} == {
        "Galería": 6, "Depósito": 2}


def test_conciliacion_sin_diferencia_no_inventa_movimiento(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    area = Area(nombre="Sala", estado="activo")
    db_session.add(area); db_session.commit()
    headers = auth_headers(usuario_admin)
    assert client.post(f"/api/v1/kardex/articulos/{articulo.id}/apertura",
                       headers=headers, json={"cantidad": 5,
                       "referencia_documento": "ACTA-01",
                       "justificacion": "Conteo físico verificado",
                       "conteo_verificado": True}).status_code == 200
    respuesta = client.post(
        f"/api/v1/kardex/articulos/{articulo.id}/conciliacion-inicial",
        headers=headers, json=datos([{"area_id": area.id, "cantidad": 5}], usuario_admin.id),
    )
    assert respuesta.status_code == 200, respuesta.json()
    assert respuesta.json()["registro"]["ajuste_movimiento_id"] is None
    assert db_session.query(MovimientoKardex).count() == 0
    assert db_session.get(ConciliacionInicial, articulo.id).cantidad_fisica == 5


def test_conciliacion_bloquea_movimientos_y_sustituye_distribucion_parcial(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, segundo = activos_prueba
    area = Area(nombre="Sala", estado="activo")
    db_session.add(area); db_session.commit()
    headers = auth_headers(usuario_admin)
    for art in (articulo, segundo):
        assert client.post(f"/api/v1/kardex/articulos/{art.id}/apertura",
                           headers=headers, json={"cantidad": 5,
                           "referencia_documento": "ACTA-01",
                           "justificacion": "Conteo físico verificado",
                           "conteo_verificado": True}).status_code == 200
    assert client.post("/api/v1/kardex/movimiento-actual", headers=headers,
                       json={"articulo_id": articulo.id,
                             "solicitud_id": "99999999-9999-4999-8999-999999999999",
                             "tipo": "ingreso",
                             "cantidad": 1, "nodo_grafo": "Inventario / Compra",
                             "referencia_documento": "FACT-COMPRA-01"}).status_code == 200
    assert client.post(f"/api/v1/kardex/articulos/{segundo.id}/asignar-area",
                       headers=headers, json={"area_id": area.id, "cantidad": 1,
                       "encargado_id": usuario_admin.id,
                       "referencia_documento": "ACTA-02",
                       "justificacion": "Ubicación inicial verificada"}).status_code == 200
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/conciliacion-inicial"
    assert client.get(ruta, headers=headers).json()["estado"] == "NO_DISPONIBLE"
    assert client.post(ruta, headers=headers,
                       json=datos([{"area_id": area.id, "cantidad": 5}], usuario_admin.id)).status_code == 409
    ruta_segundo = f"/api/v1/kardex/articulos/{segundo.id}/conciliacion-inicial"
    assert client.get(ruta_segundo, headers=headers).json()["estado"] == "DISPONIBLE"
    respuesta = client.post(ruta_segundo, headers=headers,
                            json=datos([{"area_id": area.id, "cantidad": 5}], usuario_admin.id))
    assert respuesta.status_code == 200, respuesta.json()
    assert respuesta.json()["registro"]["distribucion_anterior"]["sin_ubicacion_confirmada"] == 4
    assert respuesta.json()["distribucion"]["areas"][0]["cantidad"] == 5
    assert db_session.query(ConciliacionInicial).count() == 1


def test_conciliacion_valida_evidencia_areas_y_permisos(
    client, db_session, usuario_admin, usuario_operador, activos_prueba,
):
    articulo, _ = activos_prueba
    activa = Area(nombre="Sala", estado="activo")
    baja = Area(nombre="Archivo", estado="baja")
    db_session.add_all([activa, baja]); db_session.commit()
    headers = auth_headers(usuario_admin)
    ruta = f"/api/v1/kardex/articulos/{articulo.id}/conciliacion-inicial"
    valido = datos([{"area_id": activa.id, "cantidad": 2}], usuario_admin.id)
    assert client.post(ruta, headers=auth_headers(usuario_operador), json=valido).status_code == 403
    assert client.post(ruta, headers=headers,
                       json={**valido, "conteo_verificado": False}).status_code == 422
    assert client.post(ruta, headers=headers,
                       json={**valido, "fecha_conteo": str(date.today() + timedelta(days=1))}).status_code == 422
    assert client.post(ruta, headers=headers,
                       json={**valido, "areas": [{"area_id": activa.id, "cantidad": 2},
                                                  {"area_id": activa.id, "cantidad": 1}]}).status_code == 422
    assert client.post(ruta, headers=headers,
                       json={**valido, "areas": [{"area_id": baja.id, "cantidad": 2}]}).status_code == 422
    assert db_session.query(ConciliacionInicial).count() == 0
