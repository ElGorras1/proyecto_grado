from datetime import date

from app.models.cobertura import CoberturaArticulo, TramoCobertura
from app.models.kardex import LoteCarga
from test_kardex import activos_prueba, auth_headers, crear_movimiento, usuario_auditor


def test_cobertura_distingue_evidencia_observada_de_revision_humana(
    client, db_session, usuario_auditor, usuario_operador, activos_prueba,
):
    articulo, _ = activos_prueba
    ruta = f"/api/v1/kardex/cobertura/{articulo.id}"
    lote = LoteCarga(total_imagenes=2, tanda=1)
    db_session.add(lote)
    db_session.commit()
    crear_movimiento(db_session, articulo_id=articulo.id, lote_id=lote.id,
                     fecha=date(2024, 1, 1), saldo=8, ingresos=8,
                     numero_pagina=1, orden_fila=1)
    inicial = client.get(ruta, headers=auth_headers(usuario_auditor)).json()
    assert inicial["evidencia_disponible"]["paginas_con_filas"] == 1
    assert inicial["evidencia_disponible"]["lotes"][0]["paginas_declaradas"] == 2
    assert inicial["revision"]["estado"] == "SIN_CONFIRMAR"
    assert not inicial["revision"]["vigente"]

    tramo = {"gestion_desde": 2025, "gestion_hasta": 2026,
             "estado": "PENDIENTE", "paginas_faltantes": None,
             "descripcion": "Falta localizar el cierre de estas gestiones",
             "referencia": "Acta de revisión 01"}
    assert client.post(ruta + "/tramos", json=tramo,
                       headers=auth_headers(usuario_operador)).status_code == 403
    assert client.post(ruta + "/tramos", json=tramo,
                       headers=auth_headers(usuario_auditor)).status_code == 201
    assert db_session.query(TramoCobertura).count() == 1
    revision = {"estado": "PARCIAL", "referencia": "Acta de revisión 01",
                "observacion": "No se dispone de las hojas del cierre"}
    assert client.put(ruta + "/revision", json=revision,
                      headers=auth_headers(usuario_auditor)).status_code == 200
    assert client.put(ruta + "/revision", json=revision,
                      headers=auth_headers(usuario_auditor)).status_code == 200
    assert db_session.query(CoberturaArticulo).count() == 1
    assert client.get(ruta, headers=auth_headers(usuario_auditor)).json()["revision"]["vigente"]

    lote_nuevo = LoteCarga(total_imagenes=1, tanda=2)
    db_session.add(lote_nuevo)
    db_session.commit()
    crear_movimiento(db_session, articulo_id=articulo.id, lote_id=lote_nuevo.id,
                     fecha=date(2025, 1, 1), saldo=9, ingresos=1,
                     numero_pagina=1, orden_fila=1)
    actual = client.get(ruta, headers=auth_headers(usuario_auditor)).json()
    assert actual["evidencia_disponible"]["movimientos"] == 2
    assert actual["revision"]["estado"] == "PARCIAL"
    assert actual["revision"]["vigente"] is False
    assert actual["tramos"][0]["estado"] == "PENDIENTE"


def test_no_se_confirma_cierre_sin_escaneos(client, usuario_auditor, activos_prueba):
    articulo, _ = activos_prueba
    ruta = f"/api/v1/kardex/cobertura/{articulo.id}/revision"
    r = client.put(ruta, headers=auth_headers(usuario_auditor), json={
        "estado": "CIERRE_CONFIRMADO", "referencia": "Acta 123",
        "observacion": "Se verificó la última hoja del archivo"})
    assert r.status_code == 409
