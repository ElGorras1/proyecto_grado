"""N01: una fecha incompleta nunca se convierte en un día supuesto."""

from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.models.kardex import MovimientoKardex
from app.schemas.kardex import FilaKardex, ExtraccionKardexHoja
from app.services.kardex_service import procesar_y_guardar_lote
from app.services.datos_analitica import leer_corte
from app.services.inventario import base_kardex_dict
import test_kardex as fixtures_kardex
from test_kardex import auth_headers

activos_prueba = fixtures_kardex.activos_prueba


@pytest.mark.parametrize(
    "precision,texto", [("AUSENTE", None), ("PARCIAL", "08/2023"), ("ILEGIBLE", "8-?-23")]
)
def test_extractor_conserva_fecha_incompleta(precision, texto):
    fila = FilaKardex(
        fecha=None,
        fecha_precision=precision,
        fecha_documental_texto=texto,
        detalle="INGRESO",
        ingresos=5,
        saldo_registrado=5,
        orden_fila=1,
    )
    assert fila.fecha is None
    assert fila.fecha_documental_texto == texto
    with pytest.raises(ValidationError):
        FilaKardex(**(fila.model_dump() | {"fecha": date(2023, 1, 1)}))


def test_rechaza_fecha_parcial_sin_texto_y_completa_sin_dia():
    for datos in (
        {"fecha_precision": "PARCIAL"},
        {"fecha_precision": "COMPLETA"},
        {"fecha_precision": "AUSENTE", "fecha_documental_texto": "2023"},
    ):
        with pytest.raises(ValidationError):
            FilaKardex(detalle="INGRESO", ingresos=5, saldo_registrado=5, orden_fila=1, **datos)


@pytest.fixture
def hoja_sin_fecha(db_session, activos_prueba):
    a, _ = activos_prueba
    paginas = [
        ExtraccionKardexHoja(
            nombre_articulo=a.nombre,
            filas=[
                FilaKardex(
                    fecha="2023-08-08",
                    detalle="INGRESO",
                    ingresos=5,
                    saldo_registrado=5,
                    orden_fila=1,
                ),
                FilaKardex(
                    fecha=None,
                    fecha_precision="PARCIAL",
                    fecha_documental_texto="09/2023",
                    detalle="SALIDA",
                    salidas=1,
                    saldo_registrado=4,
                    orden_fila=2,
                ),
                FilaKardex(
                    fecha=None, detalle="SALIDA", salidas=1, saldo_registrado=3, orden_fila=3
                ),
                FilaKardex(
                    fecha="2023-07-01",
                    detalle="SALIDA",
                    salidas=1,
                    saldo_registrado=2,
                    orden_fila=4,
                ),
            ],
        )
    ]
    lote = procesar_y_guardar_lote(db_session, a.id, paginas, ["storage/prueba.webp"])
    filas = (
        db_session.query(MovimientoKardex)
        .filter_by(lote_id=lote.id)
        .order_by(MovimientoKardex.orden_fila)
        .all()
    )
    for f in filas:
        f.area_estado = "NO_APLICA"
        f.requiere_auditoria_nodo = False
        f.referencia_estado = "AUSENTE"
    db_session.commit()
    return a, filas


def test_ingestion_null_no_rompe_saldos_ni_oculta_retroceso(hoja_sin_fecha):
    _, filas = hoja_sin_fecha
    assert [f.saldo_registrado for f in filas] == [5, 4, 3, 2]
    assert filas[1].fecha_estado == "FECHA_PARCIAL"
    assert filas[2].fecha_estado == "SIN_FECHA_DOCUMENTAL"
    assert filas[1].datos_originales["fecha"] is None
    assert filas[3].tiene_error_fecha


def test_reportes_csv_grafo_cobertura_sin_gestion_inventada(client, usuario_admin, hoja_sin_fecha):
    a, filas = hoja_sin_fecha
    h = auth_headers(usuario_admin)
    anual = client.get(
        "/api/v1/reportes/inventario", headers=h, params={"gestion": 2023, "origen": "historico"}
    )
    assert anual.status_code == 200, anual.text
    assert anual.json()["resumen"]["movimientos"] == 2
    sin_fecha = client.get("/api/v1/reportes/inventario", headers=h)
    assert sin_fecha.json()["gestion"] is None
    assert sin_fecha.json()["resumen"]["movimientos"] == 2
    assert all(f["gestion_confirmada"] is None for f in sin_fecha.json()["filas"])
    csv = client.get("/api/v1/reportes/inventario.csv", headers=h)
    assert csv.status_code == 200 and "09/2023" in csv.text
    assert "sin_gestion_confirmada" in csv.headers["content-disposition"]
    grafo = client.get(f"/api/v1/kardex/articulos/{a.id}/trazabilidad", headers=h).json()
    assert grafo["total"] == 4
    grafo_anual = client.get(
        f"/api/v1/kardex/articulos/{a.id}/trazabilidad",
        headers=h,
        params={"desde": "2023-01-01", "hasta": "2023-12-31"},
    ).json()
    assert grafo_anual["total"] == 2
    desconocidos = client.get(
        f"/api/v1/kardex/articulos/{a.id}/trazabilidad", headers=h, params={"sin_fecha": True}
    ).json()
    assert desconocidos["total"] == 2 and all(f["fecha"] is None for f in desconocidos["eventos"])
    reglas = client.get(
        "/api/v1/analitica/reglas-historicas", headers=h, params={"seleccion": "todos"}
    ).json()
    assert len(reglas["filas"]) == 4
    sin = next(f for f in reglas["filas"] if f["id"] == filas[1].id)
    assert sin["gestion"] is None and sin["fecha_documental_texto"] == "09/2023"
    cobertura = client.get(f"/api/v1/kardex/cobertura/{a.id}", headers=h)
    assert cobertura.status_code == 200, cobertura.text
    assert any(
        g["gestion"] is None and g["movimientos"] == 2
        for g in cobertura.json()["evidencia_disponible"]["gestiones_con_filas"]
    )


def test_hil_sin_fecha_preserva_primera_lectura_y_no_confirma_hipotesis(
    client, usuario_operador, db_session, hoja_sin_fecha
):
    a, filas = hoja_sin_fecha
    f = filas[0]
    h = auth_headers(usuario_operador)
    previo = f.fecha_movimiento
    url = f"/api/v1/kardex/movimiento/{f.id}"
    payload = {
        "saldo_registrado": f.saldo_registrado,
        "motivo": "La fotografía muestra la celda de fecha vacía.",
    }
    r = client.put(url, headers=h, json=payload | {"decision_fecha": "ausente"})
    assert r.status_code == 200, r.text
    assert r.json()["fecha_movimiento"] is None
    assert r.json()["fecha_original"] == previo.isoformat()
    assert r.json()["datos_originales"]["fecha"] == previo.isoformat()
    assert (
        client.put(
            url, headers=h, json=payload | {"decision_fecha": "confirmar_documento"}
        ).status_code
        == 422
    )
    r = client.put(
        url,
        headers=h,
        json=payload
        | {"decision_fecha": "corregir", "fecha_movimiento": "2023-08-09", "origen_fecha": "FOTO"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["fecha_original"] == previo.isoformat()
    assert r.json()["fecha_precision"] == "COMPLETA"
    nunca = filas[2]
    url = f"/api/v1/kardex/movimiento/{nunca.id}"
    for fecha in ("2023-08-10", "2023-08-11"):
        r = client.put(
            url,
            headers=h,
            json={
                "saldo_registrado": nunca.saldo_registrado,
                "motivo": "Fecha acreditada al cotejar la fuente documental.",
                "decision_fecha": "corregir",
                "fecha_movimiento": fecha,
                "origen_fecha": "FOTO",
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["fecha_original"] is None


def test_analitica_conserva_null_y_excluye_fila_sin_fecha(db_session, hoja_sin_fecha):
    _, filas = hoja_sin_fecha
    corte = leer_corte(db_session)
    assert set(corte["exclusiones"]["fecha_no_documentada"]) == {filas[1].id, filas[2].id}
    assert corte["perfil"]["por_gestion"]["SIN_GESTION_CONFIRMADA"]["disponibles"] == 2
    assert base_kardex_dict(filas[2])["operable"] is False


def test_base_de_datos_no_admite_operacion_digital_sin_fecha(db_session, activos_prueba):
    a, _ = activos_prueba
    db_session.add(
        MovimientoKardex(
            articulo_id=a.id,
            lote_id=None,
            fecha_movimiento=None,
            detalle="Digital inválido",
            saldo_registrado=0,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
