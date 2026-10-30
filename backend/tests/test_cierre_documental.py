from datetime import date
from types import SimpleNamespace

import pytest
from app.models.cobertura import CoberturaArticulo
from app.models.kardex import LoteCarga, MovimientoKardex
from app.services import cierre_documental as fuentes
from app.services.inventario import asegurar_apertura_desde_kardex, base_kardex_dict, ultimo_cierre_kardex
from test_kardex import activos_prueba, auth_headers, crear_movimiento, usuario_auditor


@pytest.fixture
def documento(db_session, activos_prueba, tmp_path, monkeypatch):
    monkeypatch.setattr(fuentes, "RAIZ_STORAGE", tmp_path)
    foto = tmp_path / "hoja.png"
    from PIL import Image
    Image.new("RGB", (5, 5)).save(foto)
    articulo, _ = activos_prueba
    lote = LoteCarga(total_imagenes=1)
    db_session.add(lote)
    db_session.commit()
    fila = crear_movimiento(db_session, articulo_id=articulo.id, lote_id=lote.id,
                            fecha=date(2024, 12, 31), saldo=8, ingresos=8,
                            numero_pagina=1, orden_fila=1)
    fila.ruta_imagen_respaldo = "storage/hoja.png"
    db_session.commit()
    return articulo, fila, foto


def cargar(client, articulo, usuario):
    return client.get(f"/api/v1/kardex/cobertura/{articulo.id}", headers=auth_headers(usuario)).json()


def confirmar(client, articulo, fila, usuario, datos=None, **cambios):
    datos = datos or cargar(client, articulo, usuario)
    payload = dict(estado="CIERRE_CONFIRMADO", referencia="Carpeta 01 · cierre 2024",
                   observacion="Cotejo de la fila final y del periodo en la fotografía original.",
                   cierre_movimiento_id=fila.id, huella_fuente_esperada=datos["huella_fuente"],
                   evidencia_revisada=True)
    payload.update(cambios)
    return client.put(f"/api/v1/kardex/cobertura/{articulo.id}/revision",
                      json=payload, headers=auth_headers(usuario))


def test_fuente_consistente_y_evidencia_auditada(client, db_session, documento, usuario_auditor):
    articulo, fila, foto = documento
    assert cargar(client, articulo, usuario_auditor)["fuente_cierre"]["estado"] == "PROPUESTA"
    assert confirmar(client, articulo, fila, usuario_auditor).status_code == 200
    row = db_session.get(CoberturaArticulo, articulo.id)
    assert row.cierre_movimiento_id == fila.id
    assert row.cierre_snapshot["foto_sha256"] == fuentes.foto_huella(fila.ruta_imagen_respaldo)
    assert row.cierre_snapshot["revisado_por"] == usuario_auditor.id
    headers = auth_headers(usuario_auditor)
    cobertura = cargar(client, articulo, usuario_auditor)
    assert cobertura["revision"]["vigente"]
    assert cobertura["fuente_cierre"]["estado"] == "CONFIRMADA"
    inventario = client.get("/api/v1/kardex/articulos", headers=headers).json()
    articulo_api = next(a for a in inventario if a["id"] == articulo.id)
    assert articulo_api["base_kardex"]["fuente_cierre"]["estado"] == "CONFIRMADA"
    assert articulo_api["base_kardex"]["movimiento_id"] == fila.id
    libro = client.get(f"/api/v1/kardex/articulos/{articulo.id}/kardex-digital", headers=headers).json()
    assert libro["base"]["movimiento_historico_id"] == fila.id
    assert libro["base"]["fuente_cierre"]["estado"] == "CONFIRMADA"
    from app.api.v1.endpoints.reporte_institucional import construir
    informe = construir(db_session, 2026)
    assert any(a["base_documental"]["fuente_cierre"]["estado"] == "CONFIRMADA"
               for a in informe["inventario_actual"] if a["articulo_id"] == articulo.id)


@pytest.mark.parametrize("tipo", ["otro_articulo", "digital", "inactivo", "sin_foto", "sin_fecha", "sin_checkbox"])
def test_confirmacion_exige_fuente_valida(client, db_session, documento, usuario_auditor, activos_prueba, tipo):
    articulo, fila, foto = documento
    cambios = {}
    if tipo == "otro_articulo":
        fila.articulo_id = activos_prueba[1].id
    elif tipo == "digital":
        fila.lote_id = None
    elif tipo == "inactivo":
        fila.estado = "ANULADO"
    elif tipo == "sin_foto":
        foto.unlink()
    elif tipo == "sin_fecha":
        fila.fecha_movimiento = None
        fila.fecha_precision = "AUSENTE"
    else:
        cambios["evidencia_revisada"] = False
    db_session.commit()
    assert confirmar(client, articulo, fila, usuario_auditor, **cambios).status_code == 409
    assert db_session.get(CoberturaArticulo, articulo.id) is None


@pytest.mark.parametrize("tipo", ["fila", "foto", "revision"])
def test_rechaza_decision_desactualizada(client, db_session, documento, usuario_auditor, tipo):
    articulo, fila, foto = documento
    datos = cargar(client, articulo, usuario_auditor)
    if tipo == "fila":
        fila.saldo_registrado = 7
        db_session.commit()
    elif tipo == "foto":
        foto.write_bytes(b"evidencia sustituida")
    else:
        assert confirmar(client, articulo, fila, usuario_auditor).status_code == 200
    assert confirmar(client, articulo, fila, usuario_auditor, datos).status_code == 409


def test_importacion_antigua_no_sustituye_y_apertura_usada_no_cambia(
    client, db_session, documento, usuario_auditor,
):
    articulo, fila, foto = documento
    assert confirmar(client, articulo, fila, usuario_auditor).status_code == 200
    apertura = asegurar_apertura_desde_kardex(db_session, articulo.id, usuario_auditor, SimpleNamespace(client=None))
    db_session.commit()
    lote = LoteCarga(total_imagenes=1)
    db_session.add(lote)
    db_session.commit()
    vieja = crear_movimiento(db_session, articulo_id=articulo.id, lote_id=lote.id,
                             fecha=date(2020, 1, 1), saldo=3, ingresos=3, numero_pagina=1, orden_fila=1)
    assert ultimo_cierre_kardex(db_session, articulo.id).id == fila.id
    fuente = fuentes.fuente_cierre(db_session, articulo.id)
    assert fuente.propuesta.id == vieja.id
    assert fuente.estado == "DESACTUALIZADA"
    assert not base_kardex_dict(fuente.cierre, fuente)["operable"]
    congelada = asegurar_apertura_desde_kardex(db_session, articulo.id, usuario_auditor, SimpleNamespace(client=None))
    assert congelada.movimiento_historico_id == fila.id and congelada.cantidad_inicial == 8
    assert congelada.aprobado_en == apertura.aprobado_en
    assert confirmar(client, articulo, fila, usuario_auditor).status_code == 200
    datos = cargar(client, articulo, usuario_auditor)
    assert datos["revision"]["vigente"]
    assert datos["continuidad"]["cierre_disponible"]["movimiento_id"] == fila.id
    d = client.get("/api/v1/reportes/dashboard?gestion=2026", headers=auth_headers(usuario_auditor)).json()
    assert d["inventario"]["saldo_ultimo_registrado"] == 8


def test_retirar_confirmacion_no_reemplaza_fuente(client, db_session, documento, usuario_auditor):
    articulo, fila, _ = documento
    assert confirmar(client, articulo, fila, usuario_auditor).status_code == 200
    r = client.put(f"/api/v1/kardex/cobertura/{articulo.id}/revision", headers=auth_headers(usuario_auditor),
                   json=dict(estado="PARCIAL", referencia="Revisión pendiente",
                             observacion="El periodo requiere un segundo cotejo del archivo."))
    assert r.status_code == 200
    fuente = fuentes.fuente_cierre(db_session, articulo.id)
    assert fuente.cierre.id == fila.id and fuente.estado == "RETIRADA"
    assert not base_kardex_dict(fuente.cierre, fuente)["operable"]


def test_operador_no_confirma(client, documento, usuario_operador):
    articulo, fila, _ = documento
    assert confirmar(client, articulo, fila, usuario_operador).status_code == 403


def test_cierre_elegido_prevalece_en_dashboard_sin_apertura(client, db_session, documento, usuario_auditor):
    articulo, fila, _ = documento
    lote = LoteCarga(total_imagenes=1)
    db_session.add(lote)
    db_session.commit()
    crear_movimiento(db_session, articulo_id=articulo.id, lote_id=lote.id,
                     fecha=date(2020, 1, 1), saldo=3, ingresos=3, numero_pagina=1, orden_fila=1)
    assert confirmar(client, articulo, fila, usuario_auditor).status_code == 200
    headers = auth_headers(usuario_auditor)
    dashboard = client.get("/api/v1/reportes/dashboard?gestion=2026", headers=headers).json()
    assert dashboard["inventario"]["saldo_ultimo_registrado"] == 8
    inventario = client.get("/api/v1/kardex/articulos", headers=headers).json()
    assert next(a for a in inventario if a["id"] == articulo.id)["stock_actual"] == 8
    fila.saldo_registrado = 7
    db_session.commit()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as error:
        asegurar_apertura_desde_kardex(db_session, articulo.id, usuario_auditor, SimpleNamespace(client=None))
    assert error.value.status_code == 409


def test_foto_fuera_de_storage_rechazada(tmp_path, monkeypatch):
    monkeypatch.setattr(fuentes, "RAIZ_STORAGE", tmp_path / "privado")
    (tmp_path / "foto.png").write_bytes(b"foto ajena")
    assert fuentes.foto_huella("storage/../foto.png") is None
