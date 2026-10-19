"""El libro digital parte del corte y concatena entradas, salidas y traslados."""
import csv
import io
from datetime import date
from uuid import uuid4

from app.models.inventario import AperturaInventario
from app.models.kardex import LoteCarga
from test_kardex import activos_prueba, auth_headers, crear_movimiento
from test_transferencias_area import escenario, datos
from test_ajustes_operativos import rectificacion


def test_base_documental_sin_corte_no_crea_apertura(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    lote = LoteCarga(total_imagenes=1)
    db_session.add(lote)
    db_session.commit()
    movimiento = crear_movimiento(db_session, articulo_id=articulo.id,
        lote_id=lote.id, fecha=date(2025, 12, 31), saldo=18,
        ingresos=18, numero_pagina=1, orden_fila=1)

    respuesta = client.get(f"/api/v1/kardex/articulos/{articulo.id}/kardex-digital",
        headers=auth_headers(usuario_admin))

    assert respuesta.status_code == 200
    libro = respuesta.json()
    assert libro["estado"] == "BASE_DOCUMENTAL_SIN_CORTE"
    assert libro["base"]["cantidad"] == 18
    assert libro["base"]["movimiento_historico_id"] == movimiento.id
    assert libro["eventos"] == []
    assert db_session.get(AperturaInventario, articulo.id) is None


def test_libro_consolida_saldo_con_transferencia_y_rectificacion(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, articulo)
    headers = auth_headers(usuario_admin)
    ingreso = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
        json={"solicitud_id": str(uuid4()), "articulo_id": articulo.id,
              "tipo": "ingreso", "cantidad": 2,
              "nodo_grafo": "Inventario / Compra",
              "tipo_operacion": "Inventario / Compra",
              "area_operativa_id": origen.id,
              "referencia_documento": "FACT-COMPRA-01"})
    assert ingreso.status_code == 200, ingreso.json()
    transferencia = client.post(
        f"/api/v1/kardex/articulos/{articulo.id}/transferencias",
        headers=headers, json=datos(origen, destino, usuario_admin))
    assert transferencia.status_code == 200, transferencia.json()
    salida = client.post("/api/v1/kardex/movimiento-actual", headers=headers,
        json={"solicitud_id": str(uuid4()), "articulo_id": articulo.id,
              "tipo": "salida", "cantidad": 1,
              "nodo_grafo": "Ventas", "tipo_operacion": "Ventas",
              "receptor": "Biblioteca", "receptor_tipo": "INSTITUCION",
              "area_operativa_id": destino.id,
              "referencia_documento": "FACT-VENTA-01"})
    assert salida.status_code == 200, salida.json()
    assert client.post(f"/api/v1/kardex/movimiento-actual/{salida.json()['id']}/corregir",
        headers=headers, json=rectificacion(0)).status_code == 200

    respuesta = client.get(f"/api/v1/kardex/articulos/{articulo.id}/kardex-digital",
        headers=headers)

    assert respuesta.status_code == 200
    libro = respuesta.json()
    assert libro["estado"] == "OPERATIVO"
    assert libro["base"]["cantidad"] == 10
    assert libro["saldo_final"] == 12
    assert libro["integridad"] is True
    assert [(e["clase"], e["saldo_institucional"]) for e in libro["eventos"]] == [
        ("OPERACION", 12), ("TRANSFERENCIA", 12),
        ("OPERACION", 11), ("OPERACION", 12)]
    assert libro["eventos"][1]["area_origen"] == origen.nombre
    assert libro["eventos"][1]["area_destino"] == destino.nombre
    assert libro["eventos"][1]["cantidad_transferida"] == 3
    assert libro["eventos"][2]["estado"] == "ACTIVO"
    assert libro["eventos"][2]["salida"] == 1
    assert libro["eventos"][2]["cantidad_original"] == 1
    assert libro["eventos"][3]["corrige_movimiento_id"] == salida.json()["id"]
    assert libro["eventos"][3]["cantidad_corregida"] == 0
    assert db_session.get(AperturaInventario, articulo.id).cantidad_actual == 12
    archivo = client.get(f"/api/v1/kardex/articulos/{articulo.id}/kardex-digital.csv",
        headers=headers)
    assert archivo.status_code == 200
    assert "attachment" in archivo.headers["content-disposition"]
    filas = list(csv.DictReader(io.StringIO(archivo.text.lstrip("\ufeff")), delimiter=";"))
    assert [fila["tipo"] for fila in filas] == ["BASE", "OPERACION", "TRANSFERENCIA", "OPERACION", "OPERACION"]
    assert [fila["saldo_institucional"] for fila in filas] == ["10", "12", "12", "11", "12"]
    assert filas[2]["cantidad_transferida"] == "3"
    assert filas[-1]["corrige_movimiento_id"] == str(salida.json()["id"])
