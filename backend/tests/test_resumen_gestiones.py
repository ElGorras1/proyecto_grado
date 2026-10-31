"""Cobertura anual y selección exacta sin presentar exclusiones como casos normales."""

from datetime import date

from app.models.activos import Activo
from app.models.auditoria_historica import ResultadoHistorico
from app.models.kardex import MovimientoKardex
from app.services.datos_analitica import seleccionar
from test_analitica import cabecera, historico, trabajo  # noqa: F401


def modelo_con_resultados(db, usuario):
    modelo = trabajo(db, usuario)
    modelo.estado = "COMPLETADO"
    modelo.plaza = None
    modelo.umbral = 0.6
    elegibles, _ = seleccionar(modelo.corte["filas"])
    for i, f in enumerate(elegibles):
        db.add(
            ResultadoHistorico(
                modelo_id=modelo.id,
                movimiento_id=f["id"],
                articulo_id=f["articulo_id"],
                gestion=int(f["fecha"][:4]),
                score=0.7 if i % 20 == 0 else 0.3,
                alerta=i % 20 == 0,
                nodo=f["nodo_grafo"],
                particion=("entrenamiento", "calibracion", "evaluacion")[i % 3],
                snapshot=f,
                contexto={},
            )
        )
    db.commit()
    return modelo


def test_resumen_gestiones_y_alertas_del_corte(client, db_session, usuario_admin, historico):
    modelo = modelo_con_resultados(db_session, usuario_admin)
    url = f"/api/v1/analitica/modelos/{modelo.id}/gestiones"
    assert client.get(url).status_code == 401
    respuesta = client.get(url, headers=cabecera(usuario_admin))
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["totales"]["analizados"] == 200
    assert datos["totales"]["alertas"] == 10
    assert datos["totales"]["no_elegibles"] == 0
    assert [(g["gestion"], g["analizados"]) for g in datos["gestiones"]] == [
        ("2022", 60),
        ("2021", 60),
        ("2020", 80),
    ]
    assert all(g["estado"] == "PUNTUACION_COMPLETA" for g in datos["gestiones"])


def test_sin_fecha_no_se_presenta_como_movimiento_normal(
    client, db_session, usuario_admin, historico
):
    fila = db_session.query(MovimientoKardex).order_by(MovimientoKardex.id).first()
    fila.fecha_movimiento = None
    db_session.commit()
    modelo = modelo_con_resultados(db_session, usuario_admin)
    datos = client.get(
        f"/api/v1/analitica/modelos/{modelo.id}/gestiones", headers=cabecera(usuario_admin)
    ).json()
    sin_fecha = next(g for g in datos["gestiones"] if g["gestion"] == "SIN_GESTION_CONFIRMADA")
    assert sin_fecha["documentales"] == 1
    assert sin_fecha["elegibles"] == sin_fecha["analizados"] == 0
    assert sin_fecha["estado"] == "SIN_ELEGIBLES"
    assert datos["totales"]["analizados"] == 199
    assert datos["totales"]["no_elegibles"] == 1


def test_puntuacion_incompleta_se_informa(client, db_session, usuario_admin, historico):
    modelo = modelo_con_resultados(db_session, usuario_admin)
    fila = db_session.query(ResultadoHistorico).filter_by(modelo_id=modelo.id, gestion=2020).first()
    db_session.delete(fila)
    db_session.commit()
    datos = client.get(
        f"/api/v1/analitica/modelos/{modelo.id}/gestiones", headers=cabecera(usuario_admin)
    ).json()
    anual = next(g for g in datos["gestiones"] if g["gestion"] == "2020")
    assert anual["elegibles"] == 80 and anual["analizados"] == 79
    assert anual["elegibles_sin_puntuar"] == 1
    assert anual["estado"] == "PUNTUACION_PARCIAL"


def test_articulo_exacto_no_mezcla_titulos_parecidos(client, db_session, usuario_admin, historico):
    otro = Activo(
        nombre=historico.nombre + " suplemento", codigo="HIS-2", categoria_id=historico.categoria_id
    )
    db_session.add(otro)
    db_session.flush()
    original = db_session.query(MovimientoKardex).first()
    campos = {
        c.name: getattr(original, c.name)
        for c in MovimientoKardex.__table__.columns
        if c.name not in {"id", "articulo_id", "fecha_movimiento"}
    }
    db_session.add(
        MovimientoKardex(**campos, articulo_id=otro.id, fecha_movimiento=date(2025, 1, 1))
    )
    db_session.commit()
    modelo = modelo_con_resultados(db_session, usuario_admin)
    base = {"modelo_id": modelo.id, "articulo": "Historia institucional"}
    h = cabecera(usuario_admin)
    assert client.get("/api/v1/analitica/resultados", params=base, headers=h).json()["total"] == 201
    datos = client.get(
        "/api/v1/analitica/resultados",
        params={**base, "articulo_id": otro.id, "gestion": 2025},
        headers=h,
    ).json()
    assert datos["total"] == 1 and datos["filas"][0]["articulo_id"] == otro.id
    assert (
        client.get(
            "/api/v1/analitica/resultados", params={**base, "articulo_id": 0}, headers=h
        ).status_code
        == 422
    )
