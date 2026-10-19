from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import joblib
import pytest
import test_analitica as fixtures_analitica
from test_analitica import cabecera

from app.models.analitica_operativa import ModeloOperativo, ResultadoOperativo
from app.models.control_alertas import CasoControl
from app.models.inventario import AperturaInventario
from app.models.kardex import MovimientoKardex
from app.services import analitica_operativa as servicio
from app.services.control_alertas import registrar_caso

historico = fixtures_analitica.historico


@pytest.mark.parametrize("corte", [[], [{}], [{"registrado_en": None}]])
def test_modelo_con_corte_invalido_no_interrumpe_controles(
    corte, historico, usuario_admin, db_session
):
    db_session.add(
        ModeloOperativo(
            id=str(uuid4()),
            estado="COMPLETADO",
            activo=1,
            usuario_id=usuario_admin.id,
            configuracion={},
            corte=corte,
            huella="0" * 64,
            umbral=0.5,
        )
    )
    ahora = datetime.now(UTC)
    fila = MovimientoKardex(
        articulo_id=historico.id,
        fecha_movimiento=ahora.date(),
        detalle="Operación aislada con aviso determinístico",
        salidas=1,
        saldo_registrado=99,
        registrado_en=ahora,
        ocurrido_en=ahora,
        encargado_id=usuario_admin.id,
        alertas_control=[{"codigo": "FUERA_HORARIO", "nivel": "medio"}],
    )
    db_session.add(fila)
    db_session.flush()
    caso = registrar_caso(db_session, fila, "MOVIMIENTO")
    db_session.commit()
    assert caso.codigos == ["FUERA_HORARIO"]
    assert db_session.query(ResultadoOperativo).count() == 0


@pytest.fixture
def operaciones(historico, usuario_admin, db_session):
    a, u, db = historico, usuario_admin, db_session
    ultimo = db.query(MovimientoKardex.id).order_by(MovimientoKardex.id.desc()).first()[0]
    inicio = datetime(2026, 1, 1, 12, tzinfo=UTC)
    db.add(
        AperturaInventario(
            articulo_id=a.id,
            cantidad_inicial=10000,
            cantidad_actual=9300,
            cantidad_sin_ubicacion=9300,
            ultimo_moderno_id=ultimo,
            aprobado_por=u.id,
            aprobado_en=inicio,
            referencia_documento="ACTA-QA",
            justificacion="Conteo ficticio para prueba aislada",
        )
    )
    for i in range(125):
        momento = inicio + timedelta(days=i)
        db.add(
            MovimientoKardex(
                articulo_id=a.id,
                lote_id=None,
                fecha_movimiento=momento.date(),
                detalle="Venta ficticia de prueba",
                ingresos=None,
                salidas=(i % 7) + 1,
                saldo_registrado=10000 - i * 5,
                registrado_en=momento,
                ocurrido_en=momento - timedelta(minutes=10),
                encargado_id=u.id,
                usuario_registrador_id=u.id,
                referencia_documento="QA-" + str(i),
                tipo_operacion="Ventas",
                receptor="Institución de prueba",
                estado="ACTIVO",
            )
        )
    db.commit()
    return a


def test_falta_de_datos_no_entrena_ni_inventa_operaciones(
    client, usuario_admin, historico, db_session
):
    h = cabecera(usuario_admin)
    p = client.get("/api/v1/analitica-operativa/perfil", headers=h).json()
    assert p["total"] == 0 and p["controles_deterministicos_activos"]
    assert not p["suficientes"]
    r = client.post("/api/v1/analitica-operativa/entrenar", json={}, headers=h)
    assert r.status_code == 422
    assert db_session.query(ModeloOperativo).count() == 0


def test_modelo_se_activa_y_predice_en_transaccion_sin_reentrenar(
    operaciones, usuario_admin, usuario_operador, db_session, client, tmp_path, monkeypatch
):
    monkeypatch.setattr(servicio, "ARTEFACTOS", tmp_path)
    h = cabecera(usuario_admin)
    m = client.post("/api/v1/analitica-operativa/entrenar", json={}, headers=h)
    assert m.status_code == 201, m.text
    id = m.json()["id"]
    assert m.json()["metricas"]["entrenamiento"] == 100
    assert m.json()["metricas"]["calibracion"] == 25
    assert not m.json()["activo"]
    activar = f"/api/v1/analitica-operativa/modelos/{id}/activar"
    motivo = {"motivo": "Activación exclusivamente en prueba aislada"}
    assert client.post(activar, json=motivo, headers=cabecera(usuario_operador)).status_code == 403
    assert client.post(activar, json=motivo, headers=h).json()["activo"]

    def no_fit(*args, **kwargs):
        raise AssertionError("La inferencia nunca debe ejecutar fit")

    monkeypatch.setattr(servicio.IsolationForest, "fit", no_fit)
    momento = datetime(2026, 6, 1, 12, tzinfo=UTC)
    nuevo = MovimientoKardex(
        articulo_id=operaciones.id,
        fecha_movimiento=momento.date(),
        detalle="Caso ficticio de magnitud elevada",
        salidas=8000,
        saldo_registrado=1300,
        registrado_en=momento,
        ocurrido_en=momento,
        encargado_id=usuario_admin.id,
        usuario_registrador_id=usuario_admin.id,
        tipo_operacion="Ventas",
        referencia_documento="QA-ULTIMO",
    )
    db_session.add(nuevo)
    db_session.flush()
    anterior = db_session.get(AperturaInventario, operaciones.id).cantidad_actual
    registrar_caso(db_session, nuevo, "MOVIMIENTO")
    db_session.commit()
    r = db_session.query(ResultadoOperativo).one()
    assert r.alerta
    assert r.contexto["referencias"] == 100
    assert db_session.query(CasoControl).one().codigos == ["ISOLATION_OPERATIVO"]
    registrar_caso(db_session, nuevo, "MOVIMIENTO")
    assert db_session.query(ResultadoOperativo).count() == 1
    assert db_session.get(AperturaInventario, operaciones.id).cantidad_actual == anterior
    assert client.get("/api/v1/analitica-operativa/resultados", headers=h).json()["total"] == 1


def test_archivo_alterado_impide_activar_sin_deserializar(
    operaciones, usuario_admin, client, tmp_path, monkeypatch
):
    monkeypatch.setattr(servicio, "ARTEFACTOS", tmp_path)
    h = cabecera(usuario_admin)
    id = client.post("/api/v1/analitica-operativa/entrenar", json={}, headers=h).json()["id"]
    with (tmp_path / (id + ".joblib")).open("ab") as f:
        f.write(b"alterado")

    def prohibido(*args, **kwargs):
        raise AssertionError("No abrir un joblib alterado")

    monkeypatch.setattr(joblib, "load", prohibido)
    assert (
        client.post(
            f"/api/v1/analitica-operativa/modelos/{id}/activar",
            headers=h,
            json={"motivo": "Activación de prueba con archivo corrupto"},
        ).status_code
        == 409
    )


def test_calibracion_no_comparte_fechas_y_rectificaciones_se_excluyen(operaciones, db_session):
    filas, _ = servicio.capturar(db_session)
    train, cal = servicio.dividir(filas)
    assert max(servicio.fecha(f["registrado_en"]) for f in train) < min(
        servicio.fecha(f["registrado_en"]) for f in cal
    )
    fila = db_session.query(MovimientoKardex).filter(MovimientoKardex.lote_id.is_(None)).first()
    db_session.add(
        MovimientoKardex(
            articulo_id=operaciones.id,
            fecha_movimiento=date(2026, 5, 1),
            detalle="Rectificación de prueba",
            ingresos=1,
            saldo_registrado=9301,
            corrige_movimiento_id=fila.id,
        )
    )
    db_session.commit()
    fs, omitidos = servicio.capturar(db_session)
    assert len(fs) == 124 and omitidos["rectificados"] == 1
