from datetime import date
from io import BytesIO
import pytest
from PIL import Image
from app.core.security import create_access_token
from app.models.activos import Activo, CategoriaActivo
from app.models.kardex import LoteCarga, MovimientoKardex, SolicitudCargaKardex
from app.models.auditoria import AuditoriaSistema
from app.api.v1.endpoints import kardex
from app.services.kardex_service import recalcular_saldos_posteriores
from app.services.kardex_service import calcular_y_validar_saldos
from app.schemas.kardex import ExtraccionKardexHoja, FilaKardex


def headers(u):
    return {"Authorization": "Bearer " + create_access_token(subject=u.id, extra_claims={"rol": u.rol.nombre})}


def test_extraccion_preserva_original_y_no_confunde_fecha_con_saldo(db_session):
    paginas = [ExtraccionKardexHoja(nombre_articulo="Libro", filas=[
        FilaKardex(fecha=date(2020, 2, 1), detalle="Ingreso", ingresos=10, saldo_registrado=10, orden_fila=1),
        FilaKardex(fecha=date(2020, 1, 1), detalle="Salida", salidas=2, saldo_registrado=8, orden_fila=2),
    ])]
    filas = calcular_y_validar_saldos(db_session, 999, paginas, 1, ["pagina.webp"])
    assert filas[1].tiene_error_saldo is False
    assert filas[1].tiene_error_fecha is True
    assert filas[1].fecha_estado == "PENDIENTE_HIL"
    assert filas[1].datos_originales["fuente"] == "EXTRACCION_MLLM"
    assert filas[1].datos_originales["fecha"] == "2020-01-01"


@pytest.fixture
def secuencia(db_session):
    categoria = CategoriaActivo(nombre="Test calidad")
    db_session.add(categoria); db_session.flush()
    articulo = Activo(categoria_id=categoria.id, nombre="Libro de prueba", codigo="HIL-01")
    lote = LoteCarga(total_imagenes=1)
    db_session.add_all([articulo, lote]); db_session.flush()
    def fila(fecha, saldo, ingreso=None, salida=None, orden=1, lote_id=lote.id):
        m = MovimientoKardex(articulo_id=articulo.id, lote_id=lote_id, fecha_movimiento=fecha,
              detalle="Registro", ingresos=ingreso, salidas=salida, saldo_registrado=saldo,
              area_estado="NO_APLICA", referencia_estado="AUSENTE", nodo_grafo="Ventas",
              numero_pagina=1, orden_fila=orden, observaciones="Nota original que no se debe borrar")
        db_session.add(m); db_session.flush(); return m
    primero = fila(date(2026, 2, 2), 10, ingreso=10)
    segundo = fila(date(2025, 1, 1), 8, salida=2, orden=2)
    moderno = fila(date(2026, 3, 1), 7, salida=1, lote_id=None)
    db_session.commit()
    recalcular_saldos_posteriores(db_session, articulo.id)
    return articulo, primero, segundo, moderno


def test_recalculo_separa_fecha_saldo_y_respeta_notas_y_modernos(db_session, secuencia):
    a, primero, segundo, moderno = secuencia
    assert segundo.tiene_error_saldo is False
    assert segundo.tiene_error_fecha is True
    assert segundo.fecha_estado == "PENDIENTE_HIL"
    assert segundo.saldo_calculado == 8
    assert segundo.observaciones == "Nota original que no se debe borrar"
    assert moderno.saldo_calculado is None  # HIL no reescribe el ledger moderno
    segundo.fecha_estado = "CONFIRMADA_DOCUMENTO"
    db_session.commit()
    recalcular_saldos_posteriores(db_session, a.id)
    assert segundo.tiene_error_fecha and segundo.fecha_estado == "CONFIRMADA_DOCUMENTO"


def test_confirmar_fecha_conserva_hallazgo_y_queda_auditado(client, db_session, usuario_operador, secuencia):
    a, primero, segundo, moderno = secuencia
    h = headers(usuario_operador)
    url = f"/api/v1/kardex/movimiento/{segundo.id}"
    assert client.put(url, headers=h, json={"saldo_registrado": 8}).status_code == 400
    r = client.put(url, headers=h, json={"saldo_registrado": 8, "salidas": 2,
        "decision_fecha": "confirmar_documento", "motivo": "La foto confirma la fecha escrita"})
    assert r.status_code == 200, r.text
    assert r.json()["fecha_estado"] == "CONFIRMADA_DOCUMENTO"
    assert r.json()["tiene_error_fecha"] is True
    assert r.json()["fecha_original"] == "2025-01-01"
    pendientes = client.get("/api/v1/kardex/errores", headers=h, params={"articulo_id": a.id}).json()
    assert pendientes == []
    revisiones = client.get(url + "/revisiones", headers=h).json()
    assert revisiones[0]["detalle"]["motivo"] == "La foto confirma la fecha escrita"
    assert revisiones[0]["detalle"]["previo"]["fecha_estado"] == "PENDIENTE_HIL"
    assert client.put(f"/api/v1/kardex/movimiento/{moderno.id}", headers=h,
                       json={"saldo_registrado": 7, "motivo": "Intento"}).status_code == 400


def test_corregir_fecha_preserva_original_y_reportes_detectan_pendientes(client, db_session, usuario_operador, secuencia):
    a, primero, segundo, moderno = secuencia
    h = headers(usuario_operador)
    antes = client.get("/api/v1/reportes/inventario", headers=h, params={"gestion": 2025}).json()
    assert antes["resumen"]["pendientes_hil"] == 1
    r = client.put(f"/api/v1/kardex/movimiento/{segundo.id}", headers=h, json={
        "saldo_registrado": 8, "salidas": 2, "fecha_movimiento": "2026-02-03",
        "decision_fecha": "corregir", "motivo": "Corrección de lectura contrastada con la foto"})
    assert r.status_code == 200, r.text
    assert r.json()["fecha_original"] == "2025-01-01"
    assert r.json()["datos_originales"]["fecha_movimiento"] == "2025-01-01"
    assert r.json()["fecha_estado"] == "CORREGIDA"
    despues = client.get("/api/v1/reportes/inventario", headers=h, params={"gestion": 2025}).json()
    assert despues["resumen"]["movimientos"] == 0


def test_fallo_auditoria_revierte_correccion(client, db_session, usuario_operador, secuencia, monkeypatch):
    a, primero, segundo, moderno = secuencia
    def fallar(*args, **kwargs):
        raise RuntimeError("Auditoría falló")
    monkeypatch.setattr(kardex, "registrar_evento_auditoria", fallar)
    with pytest.raises(RuntimeError, match="Auditoría falló"):
        client.put(f"/api/v1/kardex/movimiento/{segundo.id}", headers=headers(usuario_operador), json={
            "saldo_registrado": 999, "salidas": 2, "motivo": "Prueba de atomicidad"})
    db_session.expire_all()
    assert db_session.get(MovimientoKardex, segundo.id).saldo_registrado == 8
    assert db_session.query(AuditoriaSistema).count() == 0


def test_dashboard_separa_operacion_historico_y_fecha(client, db_session, usuario_operador, secuencia):
    a, primero, segundo, moderno = secuencia
    h = headers(usuario_operador)
    assert client.get("/api/v1/reportes/dashboard", params={"gestion": 2026}).status_code == 401
    r = client.get("/api/v1/reportes/dashboard", headers=h, params={"gestion": 2026})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["operaciones"] == {"movimientos": 1, "ingresos": 0, "salidas": 1}
    assert d["calidad"]["movimientos_historicos"] == 2
    assert d["calidad"]["por_tipo"]["fecha"] == 1
    assert d["calidad"]["por_tipo"]["saldo"] == 0
    assert d["calidad"]["paginas"] == 1
    assert d["inventario"]["saldo_ultimo_registrado"] == 7
    assert d["prioridad"][0]["articulo_id"] == a.id


def test_paginas_repetidas_y_archivo_invalido_se_rechazan_antes_del_ocr(client, db_session, usuario_operador, secuencia, monkeypatch):
    a, *_ = secuencia
    llamadas = []
    monkeypatch.setattr(kardex, "procesar_lote_imagenes", lambda p: llamadas.append(p))
    buffer = BytesIO(); Image.new("RGB", (8, 8), color="green").save(buffer, "PNG")
    imagen = buffer.getvalue()
    respuesta = client.post("/api/v1/kardex/upload-lote", headers=headers(usuario_operador),
        data={"articulo_id": a.id}, files=[("archivos", ("1.png", imagen, "image/png")), ("archivos", ("2.png", imagen, "image/png"))])
    assert respuesta.status_code == 400 and "repetida" in respuesta.json()["detail"]
    invalidos = client.post("/api/v1/kardex/upload-lote", headers=headers(usuario_operador),
        data={"articulo_id": a.id}, files=[("archivos", ("archivo.png", b"no es imagen", "image/png"))])
    assert invalidos.status_code == 400
    assert llamadas == []
    assert db_session.query(SolicitudCargaKardex).count() == 0
