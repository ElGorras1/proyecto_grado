"""Referencia humana nueva, cegamiento, muestra congelada y denominadores."""
from copy import deepcopy

import pytest

from app.models.auditoria import AuditoriaSistema
from app.models.auditoria_historica import ResultadoHistorico, RevisionHistorica
from app.models.kardex import MovimientoKardex
from app.services import cierre_documental
from app.services.datos_analitica import huella
from app.services.validacion_independiente import ETIQUETAR, metricas, seleccionar
from test_analitica import cabecera
from test_evaluacion_analitica import historico, modelo_evaluado
from test_kardex import usuario_auditor

RUTA = "/api/v1/validacion/estudios"


@pytest.fixture
def evidencia(tmp_path, monkeypatch):
    monkeypatch.setattr(cierre_documental, "RAIZ_STORAGE", tmp_path)
    foto = tmp_path / "kardex_images/evidencia.webp"
    foto.parent.mkdir()
    foto.write_bytes(b"FOTO-QA-INMUTABLE")
    return foto


def crear(client, usuario, tipo="DOCUMENTAL", modelo=None, tamano=4):
    r = client.post(RUTA, headers=cabecera(usuario), json=dict(tipo=tipo,
        modelo_id=modelo.id if modelo else None, tamano=tamano, semilla="protocolo-c06",
        referencia_protocolo="ACTA-QA: criterios y muestreo definidos antes de revisar"))
    assert r.status_code == 201, r.text
    return r.json()


def etiquetar(client, usuario, estudio, item, etiqueta, anterior=0):
    return client.post(f"{RUTA}/{estudio['id']}/filas/{item}/etiqueta", headers=cabecera(usuario),
        json=dict(huella_estudio=estudio["huella_estudio"], revision_esperada=anterior,
            etiqueta=etiqueta, motivo="Cotejo humano ficticio en la fotografía de QA.",
            referencia="ACTA-QA-LECTURA", independiente=True))


def informe(client, usuario, e):
    r = client.get(f"{RUTA}/{e['id']}/informe.json", headers=cabecera(usuario))
    assert r.status_code == 200, r.text
    datos = r.json()
    assert datos["huella_exportacion"] == huella({k: v for k, v in datos.items() if k != "huella_exportacion"})
    assert [f["id"] for f in datos["filas"]] == seleccionar(datos["poblacion_ids"], len(datos["filas"]), datos["semilla"])
    return datos


def test_documental_no_cuenta_hil_y_exige_otro_revisor(client, db_session, historico,
        usuario_admin, usuario_auditor, usuario_operador, evidencia):
    e = crear(client, usuario_admin)
    assert e["seleccionadas"] == 4 and e["poblacion"] == 200
    antes = [(m.id, m.saldo_registrado) for m in db_session.query(MovimientoKardex)]
    assert client.get(RUTA).status_code == 401
    assert client.post(RUTA, headers=cabecera(usuario_operador), json={}).status_code == 403
    d = client.get(f"{RUTA}/{e['id']}", headers=cabecera(usuario_auditor)).json()
    ids = [i["id"] for i in d["filas"]]
    assert d["puede_etiquetar"] and len(set(ids)) == 4
    assert all(i["revision"] is None for i in d["filas"])
    assert informe(client, usuario_admin, e)["metricas"]["concordancia_filas"] is None
    assert etiquetar(client, usuario_admin, e, ids[0], "COINCIDE_DOCUMENTO").status_code == 403
    assert etiquetar(client, usuario_operador, e, ids[0], "COINCIDE_DOCUMENTO").status_code == 403
    primera = etiquetar(client, usuario_auditor, e, ids[0], "COINCIDE_DOCUMENTO")
    assert primera.status_code == 200, primera.text
    assert etiquetar(client, usuario_auditor, e, ids[0], "DIFERENCIA_DOCUMENTO").status_code == 409
    assert etiquetar(client, usuario_auditor, e, 99999, "COINCIDE_DOCUMENTO").status_code == 404
    assert etiquetar(client, usuario_auditor, e, ids[1], "LEGITIMO").status_code == 422
    for mid in ids[1:]:
        assert etiquetar(client, usuario_auditor, e, mid, "COINCIDE_DOCUMENTO").status_code == 200
    r = informe(client, usuario_admin, e)
    assert r["estado"] == "MUESTRA_COMPLETA" and r["metricas"]["concordancia_filas"] == 1
    assert r["metricas"]["precision"] is None and r["publicacion_institucional"] == "PENDIENTE"
    # Una rectificación conserva la decisión anterior y no cambia el Kárdex.
    assert etiquetar(client, usuario_auditor, e, ids[0], "DIFERENCIA_DOCUMENTO", primera.json()["id"]).status_code == 200
    assert informe(client, usuario_admin, e)["metricas"]["concordancia_filas"] == .75
    assert db_session.query(AuditoriaSistema).filter_by(accion=ETIQUETAR).count() == 5
    assert [(m.id, m.saldo_registrado) for m in db_session.query(MovimientoKardex)] == antes


def test_foto_cambiada_invalida_metricas_y_bloquea_nueva_conclusion(client, historico,
        usuario_admin, usuario_auditor, evidencia):
    e = crear(client, usuario_admin, tamano=1)
    mid = client.get(f"{RUTA}/{e['id']}", headers=cabecera(usuario_auditor)).json()["filas"][0]["id"]
    assert etiquetar(client, usuario_auditor, e, mid, "COINCIDE_DOCUMENTO").status_code == 200
    evidencia.write_bytes(b"OTRA-FOTO")
    r = informe(client, usuario_admin, e)
    assert r["estado"] == "PENDIENTE" and r["progreso"]["evidencias_no_vigentes"] == 1
    assert r["metricas"]["concordancia_filas"] is None
    assert etiquetar(client, usuario_auditor, e, mid, "COINCIDE_DOCUMENTO").status_code == 409


def test_detector_solo_evaluacion_sin_puntuaciones_ni_hil_reutilizado(client, db_session,
        modelo_evaluado, usuario_admin, usuario_auditor, evidencia):
    j = modelo_evaluado
    # Incluso una conclusión previa asistida no se traslada al nuevo estudio.
    for f in db_session.query(ResultadoHistorico).filter_by(modelo_id=j.id):
        f.estado_revision, f.etiqueta = "CERRADO", "LEGITIMO"
    db_session.commit()
    antes = deepcopy(j.corte), deepcopy(j.metricas)
    e = crear(client, usuario_admin, "DETECTOR", j, tamano=100)
    d = client.get(f"{RUTA}/{e['id']}", headers=cabecera(usuario_auditor)).json()
    assert len(d["filas"]) == 40  # población QA menor al tamaño pedido
    assert all(i["revision"] is None for i in d["filas"])
    texto = str(d)
    assert not any(k in texto for k in ("prediccion", "score", "muestra_control", "alerta", "contexto"))
    rs = {r.movimiento_id: r for r in db_session.query(ResultadoHistorico).filter_by(modelo_id=j.id)}
    assert all(rs[i["id"]].particion == "evaluacion" for i in d["filas"])
    # Etiquetas sintéticas independientes del valor predicho, para verificar la fórmula.
    verdad = {i["id"]: i["id"] % 2 == 0 for i in d["filas"]}
    for i in d["filas"]:
        assert etiquetar(client, usuario_auditor, e, i["id"],
            "INUSUAL_RELEVANTE" if verdad[i["id"]] else "LEGITIMO").status_code == 200
    r = informe(client, usuario_admin, e)
    tp = sum(rs[mid].alerta and v for mid, v in verdad.items())
    fp = sum(rs[mid].alerta and not v for mid, v in verdad.items())
    fn = sum(not rs[mid].alerta and v for mid, v in verdad.items())
    assert r["estado"] == "MUESTRA_COMPLETA"
    assert r["metricas"]["matriz"] == dict(tp=tp, fp=fp, fn=fn, tn=40-tp-fp-fn)
    assert r["metricas"]["recall"] == tp / (tp+fn)
    assert r["metricas"]["f1"] == 2*tp/(2*tp+fp+fn)
    assert not db_session.query(RevisionHistorica).count()
    assert (j.corte, j.metricas) == antes
    # Un error documental no se vuelve negativo para mejorar el denominador.
    fila = r["filas"][0]
    assert etiquetar(client, usuario_auditor, e, fila["id"], "ERROR_DOCUMENTAL", fila["revision"]["id"]).status_code == 200
    assert informe(client, usuario_admin, e)["metricas"]["matriz"] is None


def test_estudio_alterado_no_es_evaluable(client, db_session, historico, usuario_admin, evidencia):
    e = crear(client, usuario_admin)
    s = db_session.get(AuditoriaSistema, e["id"])
    datos = deepcopy(s.detalle)
    datos["items"].pop()
    s.detalle = datos
    db_session.commit()
    assert client.get(f"{RUTA}/{e['id']}", headers=cabecera(usuario_admin)).status_code == 409
    assert client.get(f"{RUTA}/{e['id']}/informe.json", headers=cabecera(usuario_admin)).status_code == 409


def test_sorteo_y_divisiones_sin_datos_no_inventan_metricas():
    assert seleccionar(range(20), 10, "s") == seleccionar(reversed(range(20)), 10, "s")
    assert seleccionar(range(20), 10, "s") != seleccionar(range(20), 10, "otra")
    from types import SimpleNamespace
    rs = {1: SimpleNamespace(detalle={"etiqueta": "LEGITIMO"})}
    r = metricas("DETECTOR", [{"id": 1, "prediccion": False}], rs, True)
    assert r["matriz"] == dict(tp=0, fp=0, fn=0, tn=1)
    assert r["precision"] is None and r["recall"] is None and r["f1"] is None
