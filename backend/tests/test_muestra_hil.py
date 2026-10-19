"""La muestra exige decisiones humanas y conserva su corte y evidencia."""

from datetime import date

from app.models.auditoria import AuditoriaSistema
from app.models.kardex import LoteCarga, MovimientoKardex
from test_kardex import activos_prueba, auth_headers, usuario_auditor


def test_muestra_congelada_con_revision_auditable(
    client, db_session, usuario_admin, usuario_auditor, usuario_operador, activos_prueba,
):
    articulo, _ = activos_prueba
    lotes = [LoteCarga(tanda=1, total_imagenes=1), LoteCarga(tanda=2, total_imagenes=1)]
    db_session.add_all(lotes)
    db_session.flush()
    filas = [
        MovimientoKardex(
            articulo_id=articulo.id, lote_id=lotes[i % 2].id,
            fecha_movimiento=date(2025, 1, i + 1), detalle=f"Fila {i}",
            ingresos=10, saldo_registrado=10, numero_pagina=1, orden_fila=i + 1,
            ruta_imagen_respaldo=f"storage/kardex_images/{i}.webp",
            tiene_error_saldo=i == 0, area_estado="NO_APLICA",
            referencia_estado="AUSENTE", estado="ACTIVO",
        ) for i in range(4)
    ]
    db_session.add_all(filas)
    db_session.commit()
    ruta = "/api/v1/kardex/muestras-validacion"
    assert client.get(ruta).status_code == 401
    assert client.post(ruta, headers=auth_headers(usuario_operador),
                       json={"tamano": 3}).status_code == 403
    creada = client.post(ruta, headers=auth_headers(usuario_admin),
                         json={"tamano": 3, "semilla": "acta-2026"})
    assert creada.status_code == 200, creada.text
    muestra_id = creada.json()["id"]
    ids = creada.json()["ids"]
    assert len(ids) == 3 and len(set(ids)) == 3
    assert creada.json()["elegibles"] == 4
    assert len(creada.json()["estratos"]) == 3

    # El corte permanece igual aunque lleguen más escaneos.
    db_session.add(MovimientoKardex(
        articulo_id=articulo.id, lote_id=lotes[1].id,
        fecha_movimiento=date(2025, 2, 1), detalle="Carga posterior",
        ingresos=1, saldo_registrado=11, numero_pagina=1, orden_fila=5,
        ruta_imagen_respaldo="storage/kardex_images/nueva.webp",
        area_estado="NO_APLICA", referencia_estado="AUSENTE", estado="ACTIVO",
    ))
    db_session.commit()
    vista = client.get(f"{ruta}/{muestra_id}", headers=auth_headers(usuario_auditor))
    assert vista.status_code == 200, vista.text
    assert [fila["id"] for fila in vista.json()["filas"]] == ids
    assert vista.json()["resumen"]["sin_revisar"] == 3
    assert vista.json()["resumen"]["coinciden"] == 0
    huella = vista.json()["filas"][0]["huella_actual"]

    revision_url = f"{ruta}/{muestra_id}/movimientos/{ids[0]}/revision"
    assert client.post(revision_url, headers=auth_headers(usuario_operador), json={
        "resultado": "COINCIDE_DOCUMENTO", "motivo": "Comparé con la fotografía",
        "huella_fila": huella,
    }).status_code == 403
    assert client.post(revision_url, headers=auth_headers(usuario_auditor), json={
        "resultado": "COINCIDE_DOCUMENTO", "motivo": "corto", "huella_fila": huella,
    }).status_code == 422
    assert client.post(revision_url, headers=auth_headers(usuario_auditor), json={
        "resultado": "COINCIDE_DOCUMENTO", "motivo": "             ", "huella_fila": huella,
    }).status_code == 422
    aprobada = client.post(revision_url, headers=auth_headers(usuario_auditor), json={
        "resultado": "COINCIDE_DOCUMENTO", "motivo": "Fecha y cantidades coinciden con la fotografía",
        "huella_fila": huella,
    })
    assert aprobada.status_code == 200, aprobada.text
    vista = client.get(f"{ruta}/{muestra_id}", headers=auth_headers(usuario_admin)).json()
    assert vista["resumen"]["coinciden"] == 1
    assert vista["filas"][0]["revision"]["revisor"] == usuario_auditor.nombre
    assert vista["filas"][0]["revision"]["vigente"] is True
    evento = db_session.query(AuditoriaSistema).filter_by(
        accion="validar_muestra_hil", recurso_id=ids[0],
    ).one()
    assert evento.detalle["ruta_imagen"] == vista["filas"][0]["ruta_imagen_respaldo"]

    db_session.get(MovimientoKardex, ids[0]).saldo_registrado = 12
    db_session.commit()
    cambiada = client.get(f"{ruta}/{muestra_id}", headers=auth_headers(usuario_auditor)).json()
    assert cambiada["resumen"]["desactualizadas"] == 1
    assert cambiada["resumen"]["coinciden"] == 0
    assert client.post(revision_url, headers=auth_headers(usuario_auditor), json={
        "resultado": "COINCIDE_DOCUMENTO", "motivo": "Decisión basada en datos anteriores",
        "huella_fila": huella,
    }).status_code == 409


def test_muestra_no_revisa_filas_ajenas(client, db_session, usuario_admin, activos_prueba):
    articulo, _ = activos_prueba
    lote = LoteCarga(tanda=2, total_imagenes=1)
    db_session.add(lote)
    db_session.flush()
    db_session.add(MovimientoKardex(
        articulo_id=articulo.id, lote_id=lote.id, fecha_movimiento=date(2025, 1, 1),
        detalle="Documento", ingresos=1, saldo_registrado=1, numero_pagina=1,
        orden_fila=1, ruta_imagen_respaldo="storage/kardex_images/1.webp",
        area_estado="NO_APLICA", referencia_estado="AUSENTE", estado="ACTIVO",
    ))
    db_session.commit()
    ruta = "/api/v1/kardex/muestras-validacion"
    creada = client.post(ruta, headers=auth_headers(usuario_admin),
                         json={"tanda": 2, "tamano": 1})
    assert creada.status_code == 200, creada.text
    muestra_id = creada.json()["id"]
    assert client.post(f"{ruta}/{muestra_id}/movimientos/999/revision",
                       headers=auth_headers(usuario_admin), json={
        "resultado": "DIFERENCIA_DOCUMENTO", "motivo": "La cifra no coincide con el papel",
        "huella_fila": "a" * 64,
    }).status_code == 404
