"""Regresiones de integridad detectadas durante la auditoría integral."""
from datetime import UTC, date, datetime
import time

import pytest

from app.api.v1.endpoints import kardex
from app.core.security import create_access_token
from app.models.activos import Activo, CategoriaActivo
from app.models.auditoria import AuditoriaSistema
from app.models.inventario import AperturaInventario
from app.models.kardex import LoteCarga, MovimientoKardex
from app.schemas.kardex import MovimientoKardexOut
from app.core.config import Settings
from app.core.security import decode_access_token
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
import jwt


def headers(usuario):
    return {"Authorization": "Bearer " + create_access_token(subject=usuario.id)}


def test_altas_en_el_mismo_segundo_son_independientes(client, db_session, usuario_operador, monkeypatch):
    h = headers(usuario_operador)
    monkeypatch.setattr(time, "time", lambda: 1792340000)
    respuestas = [client.post("/api/v1/kardex/articulos", headers=h, json={"nombre": n})
                  for n in ("Libro primero", "Libro segundo")]
    assert all(r.status_code == 200 for r in respuestas)
    assert len({r.json()["codigo"] for r in respuestas}) == 2
    assert db_session.query(Activo).count() == 2
    assert db_session.query(AuditoriaSistema).filter_by(accion="crear_articulo").count() == 2


def test_alta_fallida_no_deja_articulo_sin_auditoria(client, db_session, usuario_operador, monkeypatch):
    def fallar(*args, **kwargs):
        raise RuntimeError("Auditoría no disponible")
    monkeypatch.setattr(kardex, "registrar_evento_auditoria", fallar)
    with pytest.raises(RuntimeError, match="Auditoría no disponible"):
        client.post("/api/v1/kardex/articulos", headers=headers(usuario_operador),
                    json={"nombre": "No debe persistir"})
    assert db_session.query(Activo).count() == 0
    assert db_session.query(AuditoriaSistema).count() == 0


def test_nombre_normalizado_no_desborda_columna(client, db_session, usuario_operador):
    for nombre in ("x" * 151, "ß" * 100):
        assert client.post("/api/v1/kardex/articulos", headers=headers(usuario_operador),
                           json={"nombre": nombre}).status_code == 422
    assert db_session.query(Activo).count() == 0


def test_dashboard_respeta_orden_fisico_y_apertura(client, db_session, usuario_admin):
    cat = CategoriaActivo(nombre="Auditoría")
    db_session.add(cat); db_session.flush()
    a = Activo(categoria_id=cat.id, codigo="AUD-1", nombre="Libro")
    lote = LoteCarga(total_imagenes=1)
    db_session.add_all([a, lote]); db_session.flush()
    # La fila anterior se inserta después; el ID mayor no es el cierre.
    for orden, saldo in ((2, 8), (1, 10)):
        db_session.add(MovimientoKardex(articulo_id=a.id, lote_id=lote.id,
            fecha_movimiento=date(2025, 1, orden), detalle="Papel", saldo_registrado=saldo,
            numero_pagina=1, orden_fila=orden))
    db_session.commit()
    def resumen():
        r = client.get("/api/v1/reportes/dashboard", headers=headers(usuario_admin), params={"gestion": 2026})
        assert r.status_code == 200, r.text
        return r.json()["inventario"]
    assert resumen()["saldo_ultimo_registrado"] == 8
    db_session.add(AperturaInventario(articulo_id=a.id, cantidad_inicial=8, cantidad_actual=0,
        cantidad_sin_ubicacion=0, ultimo_moderno_id=0, aprobado_por=usuario_admin.id,
        aprobado_en=datetime.now(UTC), referencia_documento="Acta", justificacion="Conteo físico"))
    db_session.commit()
    d = resumen()
    assert d["saldo_ultimo_registrado"] == 0
    assert d["articulos_sin_stock"] == 1
    assert d["articulos_sin_movimientos"] == 0


def test_listado_no_duplica_cadena_de_revision_y_conserva_evidencia(db_session):
    cat = CategoriaActivo(nombre="Fuente")
    db_session.add(cat); db_session.flush()
    a = Activo(categoria_id=cat.id, codigo="AUD-2", nombre="Libro")
    db_session.add(a); db_session.flush()
    revision = {"motivo": "Lectura vigente", "origen_fecha": "HIPOTESIS",
                "revision_previa_enmienda_focalizada": {"motivo": "Primera lectura"}}
    m = MovimientoKardex(articulo_id=a.id, fecha_movimiento=date(2025, 1, 1), detalle="Ingreso",
                         saldo_registrado=1, revision_documental=revision)
    db_session.add(m); db_session.commit()
    salida = MovimientoKardexOut.model_validate(m).model_dump()
    assert salida["revision_documental"] == {"motivo": "Lectura vigente", "origen_fecha": "HIPOTESIS"}
    db_session.expire_all()
    assert db_session.get(MovimientoKardex, m.id).revision_documental == revision


def test_readiness_comprueba_bd_sin_exponer_excepciones(client, db_session, monkeypatch):
    assert client.get("/health/ready").json() == {"status": "ok", "database": "ok"}
    def fallar(*args, **kwargs):
        raise SQLAlchemyError("cadena de conexión privada")
    monkeypatch.setattr(db_session, "execute", fallar)
    r = client.get("/health/ready")
    assert r.status_code == 503
    assert r.json() == {"status": "unavailable", "database": "error"}
    assert "privada" not in r.text


@pytest.mark.parametrize("config", [
    {"JWT_SECRET_KEY": "corta"},
    {"JWT_SECRET_KEY": "cambiar-esta-clave-de-produccion-por-favor"},
    {"BACKEND_CORS_ORIGINS": ["*"]},
    {"BACKEND_CORS_ORIGINS": []},
    {"KARDEX_MAX_PAGINAS": 0},
])
def test_produccion_rechaza_configuracion_invalida(config):
    valores = dict(DATABASE_URL="postgresql://localhost/prueba", JWT_SECRET_KEY="x" * 40,
                   BACKEND_CORS_ORIGINS=["https://inventario.example"], ENVIRONMENT="production")
    valores.update(config)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **valores)


def test_token_sin_expiracion_o_sujeto_no_autoriza():
    from app.core.config import settings
    for claims in ({"sub": "1"}, {"exp": datetime.now(UTC).timestamp() + 60}):
        token = jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        assert decode_access_token(token) is None


def test_contadores_hil_y_grafo_descartan_filas_sin_efecto(client, db_session, usuario_admin):
    cat = CategoriaActivo(nombre="Avisos")
    db_session.add(cat); db_session.flush()
    a = Activo(categoria_id=cat.id, codigo="AUD-3", nombre="Artículo con notas")
    lote = LoteCarga(total_imagenes=1)
    db_session.add_all([a, lote]); db_session.flush()
    for orden, estado, error, area in (
        (1, "ACTIVO", True, "NO_APLICA"),
        (2, "ACTIVO", False, "PENDIENTE_HIL"),
        (3, "ANULADO_DOCUMENTO", True, "PENDIENTE_HIL"),
        (4, "NOTA_DOCUMENTAL", True, "PENDIENTE_HIL"),
    ):
        db_session.add(MovimientoKardex(articulo_id=a.id, lote_id=lote.id,
            fecha_movimiento=date(2025, 1, orden), detalle="Fuente", ingresos=1,
            saldo_registrado=orden, numero_pagina=1, orden_fila=orden,
            estado=estado, tiene_error_saldo=error, area_estado=area, nodo_grafo="Ventas"))
    db_session.commit()
    h = headers(usuario_admin)
    listado = client.get("/api/v1/kardex/articulos", headers=h).json()
    articulo = next(x for x in listado if x["id"] == a.id)
    assert articulo["alertas_rojas"] == 1
    assert articulo["alertas_amarillas"] == 1
    avisos = client.get("/api/v1/kardex/errores", headers=h).json()
    assert len(avisos) == 2
    grafo = client.get(f"/api/v1/kardex/grafo/{a.id}", headers=h).json()
    assert sum(x["value"] for x in grafo["links"]) == 2
