import test_cierre_anual as fixtures_cierre
from test_analitica import cabecera

from app.models.cierre_anual import CierreAnual
from app.models.inventario import AperturaInventario

historico = fixtures_cierre.historico
escenario = fixtures_cierre.escenario


def test_informe_separa_stock_actual_periodo_y_cierre(client, escenario, usuario_admin, db_session):
    h = cabecera(usuario_admin)
    anterior = client.get("/api/v1/reportes/institucional?gestion=2026", headers=h)
    assert anterior.status_code == 200, anterior.text
    dato = anterior.json()
    assert dato["totales_actuales"]["operativo"] == 102
    assert dato["resumen_periodo"]["eventos"] == 0
    assert all(not area["entradas"] and not area["salidas"] for area in dato["areas_operativas"])
    assert dato["cierre_vigente"] is None
    assert dato["cobertura_historica"]["porcentaje_fisico"] is None
    siguiente = client.get("/api/v1/reportes/institucional?gestion=2027", headers=h).json()
    assert siguiente["resumen_periodo"] == dict(
        eventos=5,
        ingresos_y_ajustes=7,
        salidas_y_ajustes=5,
        trasladado=35,
        rectificaciones_logisticas=0,
        por_clase={
            "TRANSFERENCIA": 1,
            "CUSTODIA_ENTREGA": 1,
            "CUSTODIA_VENTA": 1,
            "CUSTODIA_RETORNO": 1,
            "OPERACION": 1,
        },
    )
    assert siguiente["articulos_con_error_integridad"] == []
    areas = {area["id"]: area for area in siguiente["areas_operativas"]}
    origen, destino = areas[escenario[1].id], areas[escenario[2].id]
    assert (origen["entradas"], origen["salidas"], origen["custodia_actual"]) == (0, 30, 10)
    assert (destino["entradas"], destino["salidas"], destino["custodia_actual"]) == (22, 0, 0)
    traslado = next(e for e in siguiente["movimientos"] if e["clase"] == "TRANSFERENCIA")
    assert (traslado["area_origen_id"], traslado["area_destino_id"]) == (origen["id"], destino["id"])
    exportado = client.get("/api/v1/reportes/institucional/exportar.json?gestion=2027", headers=h)
    assert exportado.json()["movimientos"] == siguiente["movimientos"]
    assert "attachment" in exportado.headers["content-disposition"]
    assert db_session.query(CierreAnual).count() == 0
    assert db_session.get(AperturaInventario, escenario[0].id).cantidad_actual == 102


def test_informe_exige_sesion_y_ano_valido(client, usuario_operador):
    assert client.get("/api/v1/reportes/institucional?gestion=2026").status_code == 401
    assert (
        client.get(
            "/api/v1/reportes/institucional?gestion=10000", headers=cabecera(usuario_operador)
        ).status_code
        == 422
    )
