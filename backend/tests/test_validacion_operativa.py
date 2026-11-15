from datetime import UTC, date, datetime
from uuid import uuid4

from app.core.config import settings
from app.models.analitica_operativa import ModeloOperativo, ResultadoOperativo
from app.models.auditoria import AuditoriaSistema
from app.models.kardex import MovimientoKardex
from test_analitica import cabecera
import test_kardex as fixtures_kardex

activos_prueba = fixtures_kardex.activos_prueba
usuario_auditor = fixtures_kardex.usuario_auditor

RUTA = "/api/v1/validacion-operativa"


def preparar_puntuaciones(db, articulo, usuario):
    id_modelo = str(uuid4())
    db.add(ModeloOperativo(
        id=id_modelo, estado="COMPLETADO", activo=1, usuario_id=usuario.id,
        configuracion={}, corte=[], huella="0" * 64, umbral=0.5,
    ))
    db.flush()
    for i, prediccion in enumerate([True, False, True, False, False], start=1):
        instante = datetime(2026, 4, i, 12, tzinfo=UTC)
        fila = MovimientoKardex(
            articulo_id=articulo.id, fecha_movimiento=date(2026, 4, i), detalle="Movimiento sintético",
            salidas=2, saldo_registrado=10, registrado_en=instante, ocurrido_en=instante,
        )
        db.add(fila)
        db.flush()
        db.add(ResultadoOperativo(
            modelo_id=id_modelo, recurso=f"MOVIMIENTO:{fila.id}", articulo_id=articulo.id,
            movimiento_id=fila.id, contexto={}, alerta=prediccion, score=0.7 if prediccion else 0.3,
            snapshot={"id": fila.id, "articulo_id": articulo.id, "documento": f"QA-{i}",
                      "alertas": [{"codigo": "ISOLATION_OPERATIVO"}], "justificacion_operador": "Reservado"},
        ))
    db.commit()


def test_cotejo_sin_prediccion_y_resultados_al_cerrar_toda_la_muestra(
    client, db_session, usuario_admin, usuario_auditor, usuario_operador, activos_prueba, monkeypatch,
):
    monkeypatch.setattr(settings, "DATOS_OPERATIVOS_SIMULADOS", True)
    preparar_puntuaciones(db_session, activos_prueba[0], usuario_admin)
    admin, auditor, operador = map(cabecera, (usuario_admin, usuario_auditor, usuario_operador))
    payload = {"gestion": 2026, "limite": 5}
    assert client.get(RUTA, headers=operador).status_code == 403
    assert client.post(RUTA, headers=auditor, json=payload).status_code == 403
    assert client.post(RUTA, headers=admin, json=payload | {"gestion": 2025}).status_code == 422
    creada = client.post(RUTA, headers=admin, json=payload)
    assert creada.status_code == 201, creada.text
    datos = creada.json()
    assert datos["simulado"] and datos["poblacion"] == 5
    estudio = f"{RUTA}/{datos['id']}"
    muestra = client.get(estudio, headers=auditor).json()
    assert muestra["pendientes"] == 5 and muestra["metricas"] is None
    assert "ISOLATION_OPERATIVO" not in str(muestra)
    assert "prediccion" not in str(muestra) and "justificacion" not in str(muestra)

    etiquetas = ["ANOMALO", "ANOMALO", "NORMAL", "NORMAL", "INDETERMINADO"]
    for caso in muestra["casos"]:
        i = int(caso["evidencia"]["documento"].split("-")[1])
        url = f"{estudio}/casos/{caso['id']}"
        etiqueta = etiquetas[i - 1]
        voto = {"etiqueta": etiqueta, "motivo": "Cotejo de respaldo exclusivamente sintético"}
        if etiqueta != "INDETERMINADO":
            assert client.post(url, headers=auditor, json=voto).status_code == 422
            voto["respaldo"] = f"ACTA-QA-{i}"
        r = client.post(url, headers=auditor, json=voto)
        assert r.status_code == 200, r.text
        assert r.json()["revisor_id"] == usuario_auditor.id
        assert "prediccion" not in r.json()
        assert client.post(url, headers=auditor, json=voto).status_code == 200
        assert client.post(url, headers=admin, json=voto).status_code == 409

    cerrado = client.get(estudio, headers=auditor).json()
    assert cerrado["pendientes"] == 0 and cerrado["indeterminados"] == 1
    assert cerrado["metricas"] == {
        "verdaderos_positivos": 1, "falsos_positivos": 1, "falsos_negativos": 1, "verdaderos_negativos": 1,
        "clasificados": 4, "precision": 0.5, "sensibilidad": 0.5, "f1": 0.5,
    }
    assert db_session.query(AuditoriaSistema).filter_by(accion="cotejar_operacion").count() == 5


def test_hay_ambas_predicciones_en_una_muestra_minima(
    client, db_session, usuario_admin, activos_prueba,
):
    from app.models.validacion_operativa import CotejoOperativo

    preparar_puntuaciones(db_session, activos_prueba[0], usuario_admin)
    h = cabecera(usuario_admin)
    r = client.post(RUTA, json={"gestion": 2026, "limite": 2}, headers=h)
    assert r.status_code == 201, r.text
    muestra = db_session.query(CotejoOperativo).filter_by(estudio_id=r.json()["id"]).all()
    assert sorted(c.prediccion for c in muestra) == [False, True]
