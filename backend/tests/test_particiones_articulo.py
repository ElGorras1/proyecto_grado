from copy import deepcopy

import pytest

from app.services.particiones_articulo import (
    particionar_por_articulo,
    auditar_particiones,
    reconstruir_asignacion,
)
from app.services.isolation_historico import calcular
from app.services.datos_analitica import huella, leer_corte
from app.schemas.analitica import EntrenamientoHistorico


def datos():
    return [
        dict(
            id=a * 100 + i,
            articulo_id=a,
            lote_id=a * 10 + i // 15,
            ruta_imagen_respaldo=f"storage/{a}/{i//15}.png",
            fecha=f"2020-01-{i%28+1:02d}",
            detalle=f"Operación {a}-{i}",
            referencia="",
            area="Galería",
            ingresos=None,
            salidas=i % 9 + 1,
            saldo_registrado=200 - i,
            nodo_grafo="Ventas" if i % 3 else "Galería",
        )
        for a in range(1, 11)
        for i in range(30)
    ]


def test_articulo_lotes_y_fotos_no_cruzan_y_reconstruccion_es_independiente():
    filas = datos()
    original = deepcopy(filas)
    filas[0]["ruta_imagen_respaldo"] = filas[30]["ruta_imagen_respaldo"]
    original = deepcopy(filas)
    partes = particionar_por_articulo(filas, 42)
    assert auditar_particiones(filas, partes)["sin_cruces"]
    esperado = reconstruir_asignacion(filas, 42)
    assert partes == [esperado[f["id"]] for f in filas]
    inversas = particionar_por_articulo(filas[::-1], 42)
    assert {f["id"]: p for f, p in zip(filas, partes)} == {
        f["id"]: p for f, p in zip(filas[::-1], inversas)
    }
    assert filas == original
    cruzadas = list(partes)
    cruzadas[0] = next(p for p in partes if p != partes[0])
    assert not auditar_particiones(filas, cruzadas)["sin_cruces"]


def test_grupos_insuficientes_no_relajan_silenciosamente_la_separacion():
    filas = datos()
    for f in filas:
        f["ruta_imagen_respaldo"] = "storage/una_foto.png"
    with pytest.raises(ValueError, match="cinco grupos"):
        particionar_por_articulo(filas, 42)


def test_entrenamiento_por_articulo_usa_solo_train_y_declara_cambio_de_contexto():
    filas = datos()
    antes = huella(filas)
    config = EntrenamientoHistorico(modo="POR_ARTICULO", arboles=100).model_dump()
    modelo, contexto, umbral, metricas, resultados = calcular(filas, config)
    assert metricas["control_por_articulo"]["sin_cruces"]
    train = {
        f["articulo_id"] for f, r in zip(filas, resultados) if r["particion"] == "entrenamiento"
    }
    assert all(k[0] in train for k in contexto.cantidades)
    assert all(
        r["contexto"]["referencias"] == 0 for r in resultados if r["particion"] == "evaluacion"
    )
    assert metricas["precision_at_k"] is None and huella(filas) == antes


def test_trabajo_y_verificacion_integrada_con_articulos_distintos(
    client, db_session, usuario_admin, tmp_path
):
    from datetime import date
    from uuid import uuid4
    from app.models.activos import Activo, CategoriaActivo
    from app.models.kardex import LoteCarga, MovimientoKardex
    from app.models.auditoria_historica import ModeloHistorico, ResultadoHistorico
    from app.services.trabajador_analitica import ejecutar
    from app.services.evaluacion_analitica import diagnosticar, reproducir_artefacto
    from test_analitica import cabecera

    cat = CategoriaActivo(nombre="QA", estado="activo")
    db_session.add(cat)
    db_session.flush()
    for a in range(10):
        art = Activo(nombre=f"Libro QA {a}", codigo=f"QA-{a}", categoria_id=cat.id)
        lote = LoteCarga(total_imagenes=1)
        db_session.add_all([art, lote])
        db_session.flush()
        for i in range(30):
            db_session.add(
                MovimientoKardex(
                    articulo_id=art.id,
                    lote_id=lote.id,
                    fecha_movimiento=date(2020, 1, i % 28 + 1),
                    detalle=f"Documento {a}-{i}",
                    salidas=i % 8 + 1,
                    saldo_registrado=100 - i,
                    numero_pagina=1,
                    orden_fila=i + 1,
                    nodo_grafo="Galería",
                    ruta_imagen_respaldo=f"storage/qa_{a}.png",
                    tiene_error_saldo=False,
                    tiene_error_fecha=False,
                    fecha_estado="SIN_ALERTA",
                    area_estado="RESUELTA_AUTOMATICAMENTE",
                    referencia_estado="AUSENTE",
                    requiere_auditoria_nodo=False,
                    requiere_auditoria_referencia=False,
                    estado="ACTIVO",
                )
            )
    db_session.commit()
    r = client.post(
        "/api/v1/analitica/entrenar",
        headers=cabecera(usuario_admin),
        json={"modo": "POR_ARTICULO", "arboles": 100},
    )
    assert r.status_code == 202, r.text
    j = db_session.query(ModeloHistorico).one()
    ejecutar(db_session, j.id, tmp_path)
    assert j.estado == "COMPLETADO"
    rs = db_session.query(ResultadoHistorico).filter_by(modelo_id=j.id).all()
    assert diagnosticar(j, rs)["estado"] == "CONSISTENTE"
    assert reproducir_artefacto(j, rs, tmp_path)['estado'] == 'CONSISTENTE'
    original = deepcopy(j.corte)
    fila = next(x for x in rs if x.particion == "evaluacion")
    fila.particion = "entrenamiento"
    prueba = diagnosticar(j, rs)
    assert (
        next(c for c in prueba["comprobaciones"] if c["codigo"] == "articulos")["estado"] == "FALLO"
    )
    assert j.corte == original
