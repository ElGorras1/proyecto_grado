from copy import deepcopy

import joblib
import pytest
import test_analitica as fixtures_analitica
from test_analitica import cabecera, trabajo

from app.models.auditoria_historica import ResultadoHistorico
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.services.datos_analitica import huella
from app.services.evaluacion_analitica import diagnosticar, reproducir_artefacto
from app.services.trabajador_analitica import ejecutar

historico = fixtures_analitica.historico


@pytest.fixture
def modelo_evaluado(historico, usuario_admin, db_session, tmp_path):
    j = trabajo(db_session, usuario_admin)
    ejecutar(db_session, j.id, tmp_path)
    assert j.estado == "COMPLETADO"
    return j


def filas(db, j):
    return db.query(ResultadoHistorico).filter_by(modelo_id=j.id).all()


def comprobacion(r, codigo):
    return next(c for c in r["comprobaciones"] if c["codigo"] == codigo)


def test_reproduccion_independiente_sin_entrenar_ni_escribir(
    modelo_evaluado, db_session, tmp_path, monkeypatch
):
    from sklearn.ensemble import IsolationForest

    from app.services import isolation_historico
    from app.services.isolation_historico import Contexto

    j = modelo_evaluado
    rs = filas(db_session, j)
    antes = deepcopy([(r.snapshot, r.contexto, r.score, r.estado_revision) for r in rs])
    contenido = (tmp_path / (j.id + ".joblib")).read_bytes()

    def prohibido(*args, **kwargs):
        raise AssertionError("El evaluador no debe entrenar ni reutilizar el transformador")

    monkeypatch.setattr(IsolationForest, "fit", prohibido)
    monkeypatch.setattr(Contexto, "fit", prohibido)
    monkeypatch.setattr(Contexto, "transformar", prohibido)
    monkeypatch.setattr(isolation_historico, "calcular", prohibido)
    monkeypatch.setattr(isolation_historico, "particionar", prohibido)
    assert diagnosticar(j, rs)["estado"] == "CONSISTENTE"
    r = reproducir_artefacto(j, rs, tmp_path)
    assert r["estado"] == "CONSISTENTE"
    assert comprobacion(r, "replay")["estado"] == "OK"
    assert (tmp_path / (j.id + ".joblib")).read_bytes() == contenido
    assert [(r.snapshot, r.contexto, r.score, r.estado_revision) for r in rs] == antes
    assert not db_session.dirty and not db_session.new and not db_session.deleted


@pytest.mark.parametrize("duplicado", [False, True])
def test_detecta_fuga_de_lote_y_contenido(modelo_evaluado, db_session, duplicado):
    j, rs = modelo_evaluado, filas(db_session, modelo_evaluado)
    train = next(r for r in rs if r.particion == "entrenamiento")
    reservado = next(r for r in rs if r.particion == "evaluacion")
    nuevo = deepcopy(reservado.snapshot)
    if duplicado:
        for k in (
            "articulo_id",
            "fecha",
            "detalle",
            "referencia",
            "area",
            "ingresos",
            "salidas",
            "saldo_registrado",
        ):
            nuevo[k] = train.snapshot[k]
        reservado.gestion = train.gestion
    else:
        nuevo["lote_id"] = train.snapshot["lote_id"]
    reservado.snapshot = nuevo
    corte = deepcopy(j.corte)
    corte["filas"] = [nuevo if f["id"] == reservado.movimiento_id else f for f in corte["filas"]]
    j.corte, j.huella = corte, huella(corte["filas"])
    r = diagnosticar(j, rs)
    assert comprobacion(r, "separacion")["estado"] == "FALLO"
    assert r["estado"] == "INCONSISTENTE"
    assert r["evaluacion"]["modelo"]["precision_at_k"] is None


def test_umbral_y_referencias_no_se_dan_por_validos(modelo_evaluado, db_session):
    j, rs = modelo_evaluado, filas(db_session, modelo_evaluado)
    reservado = next(r for r in rs if r.particion == "evaluacion")
    reservado.contexto = {**reservado.contexto, "mediana": 5000}
    j.umbral += 0.01
    r = diagnosticar(j, rs)
    assert comprobacion(r, "referencias")["estado"] == "FALLO"
    assert comprobacion(r, "calibracion")["estado"] == "FALLO"
    assert r["estado"] == "INCONSISTENTE"


def test_intercambiar_lotes_enteros_no_basta_para_validar_particiones(modelo_evaluado, db_session):
    j, rs = modelo_evaluado, filas(db_session, modelo_evaluado)
    train = next(r.snapshot["lote_id"] for r in rs if r.particion == "entrenamiento")
    reservado = next(r.snapshot["lote_id"] for r in rs if r.particion == "evaluacion")
    for r in rs:
        if r.snapshot["lote_id"] == train:
            r.particion = "evaluacion"
        elif r.snapshot["lote_id"] == reservado:
            r.particion = "entrenamiento"
    d = diagnosticar(j, rs)
    assert comprobacion(d, "separacion")["estado"] == "OK"
    assert comprobacion(d, "particiones")["estado"] == "OK"
    assert comprobacion(d, "asignacion")["estado"] == "FALLO"


def test_precision_no_reduce_denominador_ni_cuenta_error_documental(
    modelo_evaluado, db_session, client, usuario_admin
):
    j = modelo_evaluado
    top = j.metricas["top_evaluacion"]
    rs = [r for r in filas(db_session, j) if r.movimiento_id in top]
    for r in rs:
        r.estado_revision, r.etiqueta = "CERRADO", "INUSUAL_RELEVANTE"
    rs[0].etiqueta = "ERROR_DOCUMENTAL"
    db_session.commit()
    url = f"/api/v1/analitica/modelos/{j.id}/evaluacion"
    h = cabecera(usuario_admin)
    v = client.get(url, headers=h).json()["modelo"]
    assert (v["k"], v["revisados_concluyentes"], v["errores_documentales"]) == (20, 19, 1)
    assert v["precision_at_k"] is None
    rs[0].etiqueta = "LEGITIMO"
    db_session.commit()
    assert client.get(url, headers=h).json()["modelo"]["precision_at_k"] == 19 / 20
    rs[0].estado_revision = "EN_REVISION"
    db_session.commit()
    assert client.get(url, headers=h).json()["modelo"]["precision_at_k"] is None
    db_session.delete(rs[0])
    db_session.commit()
    v = client.get(url, headers=h).json()["modelo"]
    assert (v["k"], v["disponibles"], v["sin_resultado"]) == (20, 19, 1)
    assert not v["seleccion_integra"] and v["precision_at_k"] is None


def test_muestra_alterada_no_publica_precision(modelo_evaluado, db_session):
    j = modelo_evaluado
    rs = filas(db_session, j)
    for r in rs:
        r.estado_revision, r.etiqueta = "CERRADO", "LEGITIMO"
    j.metricas = {**j.metricas, "top_evaluacion": [j.metricas["top_evaluacion"][0]] * 20}
    r = diagnosticar(j, rs)
    assert comprobacion(r, "muestras")["estado"] == "FALLO"
    assert r["evaluacion"]["modelo"]["ids_duplicados"] == 19
    assert r["evaluacion"]["modelo"]["precision_at_k"] is None


def test_hash_incorrecto_no_deserializa(modelo_evaluado, db_session, tmp_path, monkeypatch):
    j = modelo_evaluado
    with (tmp_path / (j.id + ".joblib")).open("ab") as f:
        f.write(b"alteracion")

    def prohibido(*args, **kwargs):
        raise AssertionError("No cargar un archivo que no coincide con su hash")

    monkeypatch.setattr(joblib, "load", prohibido)
    r = reproducir_artefacto(j, filas(db_session, j), tmp_path)
    assert r["estado"] == "INCONSISTENTE"
    assert comprobacion(r, "sha256")["estado"] == "FALLO"
    j.id = "../externo"
    assert reproducir_artefacto(j, [], tmp_path)["estado"] == "INCONSISTENTE"


def test_diagnostico_de_lectura_por_rol_sin_cargar_joblib(
    modelo_evaluado, usuario_admin, usuario_operador, db_session, client, monkeypatch
):
    rol = Rol(nombre="Auditor", estado="activo")
    db_session.add(rol)
    db_session.flush()
    auditor = Usuario(
        rol_id=rol.id,
        nombre="Auditor",
        email="auditor@test.com",
        password_hash=usuario_admin.password_hash,
        estado="activo",
    )
    db_session.add(auditor)
    db_session.commit()

    def prohibido(*args, **kwargs):
        raise AssertionError("HTTP no deserializa modelos")

    monkeypatch.setattr(joblib, "load", prohibido)
    url = f"/api/v1/analitica/modelos/{modelo_evaluado.id}/diagnostico"
    assert client.get(url).status_code == 401
    for usuario in (usuario_admin, usuario_operador, auditor):
        r = client.get(url, headers=cabecera(usuario))
        assert r.status_code == 200, r.text
        assert r.json()["estado"] == "CONSISTENTE"
        assert r.json()["reproduccion_artefacto"] == "NO_VERIFICADO"
        assert r.json()["evaluacion"]["modelo"]["precision_at_k"] is None


def test_version_pendiente_no_aparece_verificada(historico, usuario_admin, db_session):
    j = trabajo(db_session, usuario_admin)
    r = diagnosticar(j, [])
    assert r["estado"] == "NO_VERIFICADO"
    assert r["evaluacion"]["modelo"]["precision_at_k"] is None
