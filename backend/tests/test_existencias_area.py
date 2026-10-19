from datetime import date

from app.models.activos import Existencia
from app.models.area import Area
from app.models.inventario import AperturaInventario
from app.models.kardex import LoteCarga
from test_kardex import activos_prueba, auth_headers, crear_movimiento
from test_ajustes_operativos import rectificacion


def test_ubicacion_pendiente_y_movimientos_conservan_total(
    client, db_session, usuario_admin, activos_prueba,
):
    art, _ = activos_prueba
    area = Area(nombre="Depósito de prueba", estado="activo")
    lote = LoteCarga(total_imagenes=1)
    db_session.add_all([area, lote])
    db_session.commit()
    crear_movimiento(db_session, articulo_id=art.id, lote_id=lote.id,
                     fecha=date(2025, 12, 1), saldo=10, ingresos=10,
                     numero_pagina=1, orden_fila=1)
    headers = auth_headers(usuario_admin)
    ruta = f"/api/v1/kardex/articulos/{art.id}/existencias-area"
    inicial = client.get(ruta, headers=headers).json()
    assert inicial["total_institucional"] == inicial["sin_ubicacion_confirmada"] == 10
    assert inicial["areas"] == []
    payload = {"area_id": area.id, "cantidad": 6, "encargado_id": usuario_admin.id,
               "referencia_documento": "ACTA-01",
               "justificacion": "Conteo y ubicación verificados"}
    respuesta = client.post(f"/api/v1/kardex/articulos/{art.id}/asignar-area",
                            headers=headers, json=payload)
    assert respuesta.status_code == 200
    assert respuesta.json()["total_institucional"] == 10
    assert respuesta.json()["sin_ubicacion_confirmada"] == 4
    assert respuesta.json()["areas"][0]["cantidad"] == 6
    assert db_session.get(AperturaInventario, art.id).cantidad_actual == 10

    base = {"articulo_id": art.id, "solicitud_id": "11111111-1111-4111-8111-111111111111",
            "tipo": "salida", "cantidad": 5,
            "nodo_grafo": "Área: Depósito de prueba",
            "referencia_documento": "ACTA-AREA"}
    sin_area = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
                           json=base)
    assert sin_area.status_code == 409
    assert client.get(ruta, headers=headers).json()["total_institucional"] == 10
    con_area = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
                           json={**base, "area_operativa_id": area.id})
    assert con_area.status_code == 200
    assert con_area.json()["area_operativa_id"] == area.id
    distribuido = client.get(ruta, headers=headers).json()
    assert distribuido["total_institucional"] == 5
    assert distribuido["sin_ubicacion_confirmada"] == 4
    assert distribuido["areas"][0]["cantidad"] == 1
    assert db_session.query(Existencia).filter_by(activo_id=art.id).count() == 1

    correccion = client.post(f"/api/v1/kardex/movimiento-actual/{con_area.json()['id']}/corregir",
                            headers=headers, json=rectificacion(0))
    assert correccion.status_code == 200
    restaurado = client.get(ruta, headers=headers).json()
    assert restaurado["total_institucional"] == 10
    assert restaurado["areas"][0]["cantidad"] == 6
    assert restaurado["sin_ubicacion_confirmada"] == 4


def test_asignacion_no_supera_cantidad_desconocida(
    client, db_session, usuario_admin, activos_prueba,
):
    art, _ = activos_prueba
    area = Area(nombre="Biblioteca de prueba", estado="activo")
    db_session.add(area)
    db_session.commit()
    headers = auth_headers(usuario_admin)
    assert client.post(f"/api/v1/kardex/articulos/{art.id}/apertura", headers=headers,
                       json={"cantidad": 3, "referencia_documento": "ACTA-02",
                             "justificacion": "Conteo físico verificado", "conteo_verificado": True}).status_code == 200
    respuesta = client.post(f"/api/v1/kardex/articulos/{art.id}/asignar-area",
                            headers=headers, json={"area_id": area.id, "cantidad": 4,
                            "encargado_id": usuario_admin.id,
                            "referencia_documento": "ACTA-02",
                            "justificacion": "Ubicación física verificada"})
    assert respuesta.status_code == 409
    assert db_session.query(Existencia).count() == 0
