"""Exportación completa y filtrada del corte, sin convertir avisos en etiquetas humanas."""

# ruff: noqa: F811 -- pytest inyecta por nombre la fixture importada historico.

import csv
import io

from app.models.auditoria_historica import ResultadoHistorico
from test_analitica import cabecera, historico  # noqa: F401
from test_resumen_gestiones import modelo_con_resultados


def filas(respuesta):
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.content.startswith(b"\xef\xbb\xbf")
    return list(csv.DictReader(io.StringIO(respuesta.content.decode("utf-8-sig")), delimiter=";"))


def test_csv_completo_protegido_y_sin_limite_de_pagina(
    client, db_session, usuario_admin, historico
):
    m = modelo_con_resultados(db_session, usuario_admin)
    ruta = "/api/v1/analitica/resultados.csv"
    assert client.get(ruta, params={"modelo_id": m.id}).status_code == 401
    datos = filas(client.get(ruta, params={"modelo_id": m.id}, headers=cabecera(usuario_admin)))
    assert len(datos) == 200
    assert len({f["Movimiento ID"] for f in datos}) == 200
    assert all(f["Modelo"] == m.id and f["Huella del corte"] == m.huella for f in datos)
    assert all(f["Umbral"] == "0.6" and f["Estado de revisión"] == "PENDIENTE" for f in datos)
    assert sum(f["Aviso estadístico"] == "True" for f in datos) == 10
    assert all("no discrepancia confirmada" in f["Alcance"] for f in datos)
    assert all(f["Exportado en UTC"] == datos[0]["Exportado en UTC"] for f in datos)


def test_csv_iguala_filtros_y_orden_de_consulta(client, db_session, usuario_admin, historico):
    m = modelo_con_resultados(db_session, usuario_admin)
    resultados = (
        db_session.query(ResultadoHistorico)
        .filter_by(modelo_id=m.id)
        .order_by(ResultadoHistorico.id)
        .all()
    )
    m.metricas = {"top_regla": [resultados[7].movimiento_id, resultados[1].movimiento_id]}
    db_session.commit()
    h = cabecera(usuario_admin)
    for filtros in (
        {"gestion": 2021, "articulo_id": historico.id, "seleccion": "alertas"},
        {"gestion": 2020, "articulo": "HIS-1", "nodo": "Biblioteca", "estado": "PENDIENTE"},
        {"seleccion": "top_regla"},
        {"articulo_id": historico.id + 1000},
    ):
        params = {"modelo_id": m.id, "limite": 100, **filtros}
        lista = client.get("/api/v1/analitica/resultados", params=params, headers=h).json()
        datos = filas(client.get("/api/v1/analitica/resultados.csv", params=params, headers=h))
        assert len(datos) == lista["total"]
        assert [int(f["Movimiento ID"]) for f in datos] == [
            f["movimiento_id"] for f in lista["filas"]
        ]


def test_csv_preserva_snapshot_y_neutraliza_formulas(client, db_session, usuario_admin, historico):
    m = modelo_con_resultados(db_session, usuario_admin)
    r = db_session.query(ResultadoHistorico).filter_by(modelo_id=m.id).first()
    r.snapshot = {
        **r.snapshot,
        "detalle": '  =HYPERLINK("https://ejemplo.invalid")',
        "articulo": "Nombre del corte",
    }
    historico.nombre = "Nombre cambiado después del entrenamiento"
    db_session.commit()
    datos = filas(
        client.get(
            "/api/v1/analitica/resultados.csv",
            params={"modelo_id": m.id},
            headers=cabecera(usuario_admin),
        )
    )
    exportada = next(f for f in datos if int(f["Resultado ID"]) == r.id)
    assert exportada["Artículo del corte"] == "Nombre del corte"
    assert exportada["Detalle del corte"].startswith("'  =")
    db_session.refresh(r)
    assert r.snapshot["detalle"].startswith("  =")  # La protección no reescribe el original.
    assert r.revision_numero == 0 and r.estado_revision == "PENDIENTE"


def test_csv_rechaza_modelo_incompleto_y_valida_filtros(
    client, db_session, usuario_admin, historico
):
    m = modelo_con_resultados(db_session, usuario_admin)
    h = cabecera(usuario_admin)
    ruta = "/api/v1/analitica/resultados.csv"
    assert client.get(ruta, params={"modelo_id": "inexistente"}, headers=h).status_code == 404
    assert (
        client.get(ruta, params={"modelo_id": m.id, "articulo_id": 0}, headers=h).status_code == 422
    )
    m.estado = "EN_EJECUCION"
    db_session.commit()
    assert client.get(ruta, params={"modelo_id": m.id}, headers=h).status_code == 409
