"""Gestiones de Bolivia sobre las cuatro fuentes operativas, en base aislada."""

from datetime import UTC, datetime
from uuid import uuid4

import test_cierre_anual as fixtures_cierre
from test_analitica import cabecera

from app.models.analitica_operativa import ModeloOperativo, ResultadoOperativo
from app.models.control_alertas import CasoControl
from app.models.inventario import CustodiaExterna, EventoCustodiaExterna, TransferenciaArea
from app.models.kardex import MovimientoKardex

historico = fixtures_cierre.historico
escenario = fixtures_cierre.escenario


def test_gestion_usa_registro_boliviano_y_no_fecha_de_puntuacion(
    client, db_session, escenario, usuario_admin, usuario_operador
):
    a = escenario[0]
    m = ModeloOperativo(
        id=str(uuid4()),
        estado="COMPLETADO",
        usuario_id=usuario_admin.id,
        configuracion={},
        corte=[],
        huella="a" * 64,
    )
    db_session.add(m)
    db_session.flush()
    fuentes = [
        (
            "movimiento_id",
            db_session.query(MovimientoKardex)
            .filter(MovimientoKardex.registrado_en.is_not(None))
            .one(),
        ),
        ("transferencia_id", db_session.query(TransferenciaArea).one()),
        ("custodia_id", db_session.query(CustodiaExterna).one()),
        *(
            ("evento_custodia_id", x)
            for x in db_session.query(EventoCustodiaExterna).order_by(EventoCustodiaExterna.id)
        ),
    ]
    momentos = [
        datetime(2026, 1, 1, 3, 59, 59, tzinfo=UTC),  # 2025 en Bolivia
        datetime(2026, 1, 1, 4, tzinfo=UTC),
        datetime(2026, 12, 31, 23, tzinfo=UTC),
        datetime(2027, 1, 1, 3, 59, 59, tzinfo=UTC),  # todavía 2026
        datetime(2027, 1, 1, 4, tzinfo=UTC),
    ]
    resultados, casos = [], []
    for i, ((clave, fuente), momento) in enumerate(zip(fuentes, momentos)):
        fuente.registrado_en = momento
        r = ResultadoOperativo(
            modelo_id=m.id,
            recurso=f"QA:{i}",
            articulo_id=a.id,
            **{clave: fuente.id},
            creado_en=datetime(2030, 2, 1, tzinfo=UTC),
            snapshot={"registrado_en": momento.isoformat()},
            contexto={},
            score=0.5,
            alerta=i % 2 == 0,
        )
        c = CasoControl(
            articulo_id=a.id,
            **{clave: fuente.id},
            creado_en=momento,
            estado="CERRADO" if i == 1 else "PENDIENTE",
            prioridad="BAJA" if i == 2 else "ALTA",
            snapshot={},
            codigos=["AGOTA_AREA"],
        )
        db_session.add_all([r, c])
        resultados.append(r)
        casos.append(c)
    db_session.commit()
    h = cabecera(usuario_operador)
    ruta = "/api/v1/analitica-operativa/resultados"
    for gestion, indices in ((2025, [0]), (2026, [1, 2, 3]), (2027, [4]), (2030, [])):
        response = client.get(ruta, params={"gestion": gestion}, headers=h)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["total"] == len(indices)
        assert {r["id"] for r in data["filas"]} == {resultados[i].id for i in indices}
        assert data["criterio_periodo"] == "FECHA_REGISTRO_AMERICA_LA_PAZ"
    filtros = {"gestion": 2026, "articulo_id": a.id, "modelo_id": m.id, "alertas": True}
    assert client.get(ruta, params=filtros, headers=h).json()["total"] == 1
    assert (
        client.get(ruta, params=filtros | {"articulo_id": a.id + 10000}, headers=h).json()["total"]
        == 0
    )
    pagina = client.get(ruta, params={"gestion": 2026, "pagina": 2, "limite": 2}, headers=h).json()
    assert pagina["total"] == 3 and len(pagina["filas"]) == 1

    ruta = "/api/v1/control-alertas"
    assert client.get(ruta, params={"gestion": 2026}, headers=h).json()["total"] == 2
    d = client.get(ruta, params={"gestion": 2026, "estado": "TODOS"}, headers=h).json()
    assert d["total"] == 3 and sum(d["conteos"].values()) == 3
    for filtro, cantidad in (
        ({"prioridad": "ALTA"}, 1),
        ({"hasta": "2026-01-01"}, 0),
        ({"desde": "2026-12-31", "hasta": "2026-12-31"}, 2),
        ({"articulo_id": a.id + 10000}, 0),
    ):
        assert (
            client.get(ruta, params={"gestion": 2026} | filtro, headers=h).json()["total"]
            == cantidad
        )
    for ruta in (ruta, "/api/v1/analitica-operativa/resultados"):
        assert client.get(ruta).status_code == 401
        for filtro in ({"gestion": 0}, {"gestion": 9999}, {"articulo_id": 0}):
            assert client.get(ruta, params=filtro, headers=h).status_code == 422
    assert db_session.query(ResultadoOperativo).count() == 5
    assert db_session.query(CasoControl).count() == 5
