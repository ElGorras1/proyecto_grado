from copy import deepcopy

import test_analitica as fixtures_analitica
from test_analitica import cabecera, trabajo

from app.models.auditoria_historica import ResultadoHistorico
from app.services.datos_analitica import huella, leer_corte
from app.services.evaluacion_analitica import diagnosticar
from app.services.evaluacion_temporal import preparar_corte_temporal
from app.services.trabajador_analitica import ejecutar

historico = fixtures_analitica.historico


def test_plan_aplica_exclusiones_igual_que_entrenamiento(historico, usuario_admin, client):
    ruta = "/api/v1/analitica/temporal/plan?gestion_evaluacion=2022"
    h = cabecera(usuario_admin)
    assert client.get(ruta, headers=h).json()["suficiente"]
    plan = client.get(ruta + f"&excluir_articulos={historico.id}", headers=h).json()
    assert not plan["suficiente"] and sum(plan["particiones"].values()) == 0
    assert client.get(ruta + "&excluir_articulos=999999", headers=h).status_code == 422


def test_corte_anual_no_compartido_evaluado_y_verificado(
    historico, usuario_admin, db_session, tmp_path
):
    j = trabajo(db_session, usuario_admin)
    j.configuracion = {**j.configuracion, "modo": "TEMPORAL", "gestion_evaluacion": 2022}
    j.corte = preparar_corte_temporal(j.corte, 2022)
    db_session.commit()
    assert j.corte["temporal"]["suficiente"]
    ejecutar(db_session, j.id, tmp_path)
    assert j.estado == "COMPLETADO"
    rs = db_session.query(ResultadoHistorico).filter_by(modelo_id=j.id).all()
    assert {r.gestion for r in rs if r.particion == "entrenamiento"} == {2020}
    assert {r.gestion for r in rs if r.particion == "calibracion"} == {2021}
    assert {r.gestion for r in rs if r.particion == "evaluacion"} == {2022}
    assert diagnosticar(j, rs)["estado"] == "CONSISTENTE"


def test_purga_lote_entero_y_duplicados_transitivos(historico, db_session):
    corte = leer_corte(db_session)
    train = next(f for f in corte["filas"] if f["fecha"].startswith("2020"))
    futuro = next(f for f in corte["filas"] if f["fecha"].startswith("2022"))
    # Una fila futura comparte lote pasado: las veinte filas se purgan juntas.
    train["fecha"] = "2022-01-01"
    futuro.update(
        {
            k: deepcopy(train[k])
            for k in (
                "fecha",
                "detalle",
                "referencia",
                "area",
                "ingresos",
                "salidas",
                "saldo_registrado",
            )
        }
    )
    nuevo = preparar_corte_temporal(corte, 2022)
    omitidos = set(nuevo["exclusiones"]["grupos_que_cruzan_fronteras_temporales"])
    enlazados = {
        f["id"] for f in corte["filas"] if f["lote_id"] in (train["lote_id"], futuro["lote_id"])
    }
    assert enlazados <= omitidos
    assert all(str(i) not in nuevo["particiones_temporales"] for i in enlazados)
    assert huella(corte["filas"]) == huella(nuevo["filas"])


def test_insuficiencia_no_encola_modelo_y_restringe_ano_actual(
    historico, usuario_admin, usuario_operador, client, db_session
):
    h = cabecera(usuario_admin)
    plan = client.get("/api/v1/analitica/temporal/plan?gestion_evaluacion=2025", headers=h)
    assert plan.status_code == 200
    assert not plan.json()["suficiente"]
    r = client.post(
        "/api/v1/analitica/entrenar",
        headers=h,
        json={"modo": "TEMPORAL", "gestion_evaluacion": 2025},
    )
    assert r.status_code == 422
    assert r.json()["detail"]["plan"]["faltantes"]["evaluacion"] == 20
    from app.models.auditoria_historica import ModeloHistorico

    assert db_session.query(ModeloHistorico).count() == 0
    assert (
        client.get("/api/v1/analitica/temporal/plan?gestion_evaluacion=9998", headers=h).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/analitica/entrenar",
            headers=cabecera(usuario_operador),
            json={"modo": "TEMPORAL", "gestion_evaluacion": 2022},
        ).status_code
        == 403
    )
