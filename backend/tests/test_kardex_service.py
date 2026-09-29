from datetime import date

import pytest

from app.models.kardex import LoteCarga
from app.schemas.kardex import ExtraccionKardexHoja, FilaKardex
from app.services import kardex_service


def pagina(nombre: str, *, con_filas: bool = True) -> ExtraccionKardexHoja:
    filas = []
    if con_filas:
        filas.append(
            FilaKardex(
                fecha=date(2020, 1, 1),
                detalle="Saldo inicial",
                ingresos=10,
                salidas=None,
                saldo_registrado=10,
                orden_fila=1,
            )
        )
    return ExtraccionKardexHoja(nombre_articulo=nombre, filas=filas)


def test_acepta_variantes_reales_del_encabezado_y_titulo_vacio():
    problemas = kardex_service.validar_paginas_lote(
        [
            pagina('LIBRO "COMPOSITORES BOLIVIANOS"'),
            pagina("COMPOSITORAS BOLIVIANAS DE MUSICA CONTEMP. LIBRO PARTITURAS"),
            pagina("MUSICA CONTEMPORANEA (LIBRO DE PARTITURAS)"),
            pagina("COMPOSITORAS BOLIVIANAS DE MUSICA CONTEMPORANEA (LIBRO DE PARTITURA)"),
            pagina(""),
        ],
    )

    assert problemas == []


def test_solo_detiene_pagina_sin_movimientos():
    problemas = kardex_service.validar_paginas_lote(
        [pagina("DANIELLE CAILLET"), pagina("CHACO TRÁGICO", con_filas=False)],
    )

    assert problemas == ["Página 2: no contiene movimientos extraídos."]


def test_detiene_extraccion_sin_paginas():
    assert kardex_service.validar_paginas_lote([]) == [
        "El LLM no devolvió ninguna página."
    ]


def test_fallo_de_preparacion_no_deja_lote_huerfano(db_session, monkeypatch):
    def fallar_calculo(**kwargs):
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr(kardex_service, "calcular_y_validar_saldos", fallar_calculo)

    with pytest.raises(RuntimeError, match="fallo simulado"):
        kardex_service.procesar_y_guardar_lote(
            db=db_session,
            articulo_id=1,
            paginas=[pagina("ARTÍCULO")],
            imagenes_paths=["pagina.webp"],
        )

    assert db_session.query(LoteCarga).count() == 0
