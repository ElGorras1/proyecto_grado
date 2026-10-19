from datetime import date
from uuid import uuid4
import pytest
from sqlalchemy import event
from app.models.inventario import AperturaInventario
from app.models.kardex import LoteCarga, MovimientoKardex
from app.models.auditoria import AuditoriaSistema
from test_kardex import activos_prueba, usuario_auditor, auth_headers, crear_movimiento
from test_ajustes_operativos import rectificacion


def abrir(client, usuario, articulo, cantidad=10, **kwargs):
    return client.post(f"/api/v1/kardex/articulos/{articulo.id}/apertura",
        headers=auth_headers(usuario), json={"cantidad": cantidad,
        "referencia_documento": "ACTA-01", "justificacion": "Conteo físico verificado",
        "conteo_verificado": True, **kwargs})


def mover(client, usuario, articulo, tipo="salida", cantidad=3):
    payload = {"articulo_id": articulo.id, "solicitud_id": str(uuid4()), "tipo": tipo,
               "cantidad": cantidad, "nodo_grafo": "Ventas",
               "referencia_documento": "ACTA-PRUEBA"}
    respuesta = client.post("/api/v1/kardex/movimiento-actual",
                             headers=auth_headers(usuario), json=payload)
    detalle = respuesta.json().get("detail") if respuesta.status_code == 409 else None
    if isinstance(detalle, dict) and detalle.get("codigo") == "ALERTAS_CONTROL":
        payload.update(confirmacion_alertas=detalle["firma_confirmacion"],
                       motivo_alertas="Operación intencional dentro de la prueba")
        respuesta = client.post("/api/v1/kardex/movimiento-actual",
                                 headers=auth_headers(usuario), json=payload)
    return respuesta


def stock(client, usuario, articulo):
    return next(a for a in client.get("/api/v1/kardex/articulos", headers=auth_headers(usuario)).json() if a["id"] == articulo.id)["stock_actual"]


def articulo_en_catalogo(client, usuario, articulo):
    return next(a for a in client.get("/api/v1/kardex/articulos", headers=auth_headers(usuario)).json() if a["id"] == articulo.id)


def test_cierre_kardex_es_base_y_se_congela_al_primer_movimiento(
    client, db_session, usuario_admin, usuario_operador, activos_prueba,
):
    art, _ = activos_prueba
    lote_1 = LoteCarga(total_imagenes=1)
    lote_2 = LoteCarga(total_imagenes=2)
    db_session.add_all([lote_1, lote_2]); db_session.commit()
    crear_movimiento(db_session, articulo_id=art.id, lote_id=lote_1.id,
                     fecha=date(2025, 12, 1), saldo=99, numero_pagina=1, orden_fila=1)
    cierre = crear_movimiento(db_session, articulo_id=art.id, lote_id=lote_2.id,
                             fecha=date(2024, 1, 1), saldo=20, numero_pagina=2, orden_fila=3)
    catalogo = articulo_en_catalogo(client, usuario_operador, art)
    assert catalogo["stock_actual"] == 20  # manda el orden físico, no la fecha OCR
    assert catalogo["apertura"] is None
    assert catalogo["base_kardex"]["movimiento_id"] == cierre.id
    assert catalogo["base_kardex"]["operable"] is True
    assert mover(client, usuario_operador, art, cantidad=21).status_code == 400
    assert db_session.query(AperturaInventario).count() == 0
    nuevo = mover(client, usuario_operador, art, cantidad=3)
    assert nuevo.status_code == 200 and nuevo.json()["saldo_registrado"] == 17
    apertura = db_session.get(AperturaInventario, art.id)
    assert (apertura.cantidad_inicial, apertura.cantidad_actual) == (20, 17)
    assert (apertura.origen, apertura.movimiento_historico_id,
            apertura.lote_historico_id) == ("KARDEX_HISTORICO", cierre.id, lote_2.id)
    assert db_session.query(AuditoriaSistema).filter_by(accion="activar_base_kardex_inventario").count() == 1
    lote_3 = LoteCarga(total_imagenes=1)
    db_session.add(lote_3); db_session.commit()
    crear_movimiento(db_session, articulo_id=art.id, lote_id=lote_3.id,
                     fecha=date(2025, 12, 31), saldo=50, numero_pagina=1, orden_fila=1)
    assert stock(client, usuario_operador, art) == 17
    catalogo_actual = articulo_en_catalogo(client, usuario_operador, art)
    assert catalogo_actual["diferencia_documental"]["diferencia"] == 30
    assert catalogo_actual["corte_operativo"]["estado"] == "BASE_DOCUMENTAL_PROVISIONAL"
    assert cierre.saldo_registrado == 20
    assert client.post(f'/api/v1/kardex/movimiento-actual/{nuevo.json()["id"]}/anular',
                       headers=auth_headers(usuario_operador)).status_code == 410
    assert client.post(f'/api/v1/kardex/movimiento-actual/{nuevo.json()["id"]}/corregir',
                       headers=auth_headers(usuario_admin),
                       json=rectificacion(0)).status_code == 200
    assert stock(client, usuario_operador, art) == 20


def test_saldo_final_con_alerta_se_muestra_pero_no_se_usa_para_operar(
    client, db_session, usuario_operador, activos_prueba,
):
    art, _ = activos_prueba
    lote = LoteCarga(total_imagenes=1)
    db_session.add(lote); db_session.commit()
    cierre = crear_movimiento(db_session, articulo_id=art.id, lote_id=lote.id,
                             fecha=date(2025, 12, 31), saldo=7, numero_pagina=1, orden_fila=1)
    cierre.tiene_error_saldo = True
    db_session.commit()
    catalogo = articulo_en_catalogo(client, usuario_operador, art)
    assert catalogo["stock_actual"] == 7
    assert catalogo["base_kardex"]["operable"] is False
    assert mover(client, usuario_operador, art).status_code == 409
    assert db_session.query(AperturaInventario).count() == 0


def test_transferencia_interna_no_resta_el_total_global(
    client, db_session, usuario_operador, activos_prueba,
):
    art, _ = activos_prueba
    respuesta = client.post("/api/v1/kardex/movimiento-actual",
        headers=auth_headers(usuario_operador), json={
            "articulo_id": art.id, "solicitud_id": str(uuid4()), "tipo": "salida", "cantidad": 2,
            "nodo_grafo": "Área: Biblioteca", "tipo_operacion": "Transferencia Interna",
            "referencia_documento": "ACTA-TRASPASO",
        })
    assert respuesta.status_code == 409
    assert db_session.query(MovimientoKardex).count() == 0
    assert db_session.query(AperturaInventario).count() == 0


def test_apertura_permisos_cero_y_unica(client, db_session, usuario_admin, usuario_operador, usuario_auditor, activos_prueba):
    art, _ = activos_prueba
    assert stock(client, usuario_auditor, art) is None
    assert mover(client, usuario_operador, art).status_code == 409
    for usuario in (usuario_operador, usuario_auditor):
        assert abrir(client, usuario, art).status_code == 403
    assert client.post(f"/api/v1/kardex/articulos/{art.id}/apertura", json={}).status_code == 401
    assert abrir(client, usuario_admin, art, 0).status_code == 200
    assert stock(client, usuario_auditor, art) == 0
    assert abrir(client, usuario_admin, art, 55).status_code == 409
    assert db_session.query(AperturaInventario).count() == 1
    assert db_session.query(AuditoriaSistema).filter_by(accion="aprobar_apertura_inventario").count() == 1
    assert mover(client, usuario_auditor, art).status_code == 403
    assert mover(client, usuario_operador, art, "ingreso", 4).json()["saldo_registrado"] == 4


@pytest.mark.parametrize("datos", [{"cantidad": -1}, {"cantidad": 1.5}, {"cantidad": True}, {"cantidad": 2147483648}, {"conteo_verificado": False}, {"referencia_documento": "   "}, {"justificacion": "   "}])
def test_apertura_valida_conteo_y_documento(client, usuario_admin, activos_prueba, datos):
    art, _ = activos_prueba
    assert abrir(client, usuario_admin, art, **datos).status_code == 422


def test_historico_y_antecedentes_no_modifican_stock(client, db_session, usuario_admin, usuario_operador, activos_prueba):
    art, _ = activos_prueba
    previo = crear_movimiento(db_session, articulo_id=art.id, fecha=date(2026, 1, 1), saldo=999, ingresos=999)
    assert abrir(client, usuario_admin, art, 10).json()["ultimo_moderno_id"] == previo.id
    lote = LoteCarga(total_imagenes=1)
    db_session.add(lote); db_session.commit()
    historico = crear_movimiento(db_session, articulo_id=art.id, lote_id=lote.id, fecha=date(2019, 1, 1), saldo=500, ingresos=500)
    assert stock(client, usuario_admin, art) == 10
    nuevo = mover(client, usuario_operador, art).json()
    assert nuevo["saldo_registrado"] == 7
    historico.saldo_registrado = 2000
    db_session.commit()
    assert stock(client, usuario_admin, art) == 7
    r = client.post(f"/api/v1/kardex/movimiento-actual/{previo.id}/corregir",
                    headers=auth_headers(usuario_admin), json=rectificacion(0))
    assert r.status_code == 409
    assert previo.saldo_registrado == 999 and previo.estado == "ACTIVO"
    r = client.post(f'/api/v1/kardex/movimiento-actual/{nuevo["id"]}/corregir',
                    headers=auth_headers(usuario_admin), json=rectificacion(0))
    assert r.status_code == 200
    assert stock(client, usuario_admin, art) == 10
    assert historico.saldo_registrado == 2000


def test_rectificacion_no_permite_stock_negativo_actual(client, db_session, usuario_admin, activos_prueba):
    art, _ = activos_prueba
    assert abrir(client, usuario_admin, art, 0).status_code == 200
    ingreso = mover(client, usuario_admin, art, "ingreso", 5).json()
    salida = mover(client, usuario_admin, art, "salida", 5).json()
    r = client.post(f'/api/v1/kardex/movimiento-actual/{ingreso["id"]}/corregir',
                    headers=auth_headers(usuario_admin), json=rectificacion(0))
    assert r.status_code == 409
    assert stock(client, usuario_admin, art) == 0
    assert db_session.get(MovimientoKardex, ingreso["id"]).estado == "ACTIVO"
    mover(client, usuario_admin, art, "ingreso", 5)
    r = client.post(f'/api/v1/kardex/movimiento-actual/{salida["id"]}/corregir',
                    headers=auth_headers(usuario_admin), json=rectificacion(0))
    assert r.status_code == 200
    assert stock(client, usuario_admin, art) == 10
    assert db_session.get(MovimientoKardex, salida["id"]).saldo_calculado == 0


@pytest.mark.parametrize("operacion", ["apertura", "movimiento", "rectificacion"])
def test_auditoria_y_stock_son_atomicos(client, db_session, usuario_admin, activos_prueba, operacion):
    art, _ = activos_prueba
    if operacion != "apertura":
        assert abrir(client, usuario_admin, art).status_code == 200
    if operacion == "rectificacion":
        mov = mover(client, usuario_admin, art).json()
    saldo_antes = stock(client, usuario_admin, art)
    cantidad_antes = db_session.query(MovimientoKardex).count()
    def fallar(*args):
        raise RuntimeError("auditoría no disponible")
    event.listen(AuditoriaSistema, "before_insert", fallar)
    try:
        with pytest.raises(RuntimeError, match="auditoría"):
            if operacion == "apertura":
                abrir(client, usuario_admin, art)
            elif operacion == "movimiento":
                mover(client, usuario_admin, art)
            else:
                client.post(f'/api/v1/kardex/movimiento-actual/{mov["id"]}/corregir',
                            headers=auth_headers(usuario_admin), json=rectificacion(0))
    finally:
        event.remove(AuditoriaSistema, "before_insert", fallar)
        db_session.rollback()
    assert stock(client, usuario_admin, art) == saldo_antes
    assert db_session.query(MovimientoKardex).count() == cantidad_antes
    if operacion == "rectificacion":
        assert db_session.get(MovimientoKardex, mov["id"]).estado == "ACTIVO"
