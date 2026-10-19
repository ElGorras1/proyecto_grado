from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import test_analitica as fixtures_analitica
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from test_analitica import cabecera

from app.models.activos import Existencia
from app.models.area import Area
from app.models.auditoria import AuditoriaSistema
from app.models.cierre_anual import CierreAnual
from app.models.inventario import (
    AperturaInventario,
    CustodiaExterna,
    EventoCustodiaExterna,
    TransferenciaArea,
)
from app.models.kardex import MovimientoKardex
from app.services import cierre_anual as servicio

historico = fixtures_analitica.historico


@pytest.fixture
def escenario(historico, usuario_admin, db_session, monkeypatch):
    db, a, u = db_session, historico, usuario_admin
    monkeypatch.setattr(servicio, "ahora", lambda: datetime(2027, 1, 15, tzinfo=UTC))
    origen, destino = Area(nombre="Biblioteca", estado="activo"), Area(
        nombre="Venta", estado="activo"
    )
    db.add_all([origen, destino])
    db.flush()
    db.add(
        AperturaInventario(
            articulo_id=a.id,
            cantidad_inicial=100,
            cantidad_actual=102,
            cantidad_sin_ubicacion=20,
            cantidad_custodia_externa=10,
            ultimo_moderno_id=200,
            aprobado_por=u.id,
            aprobado_en=datetime(2026, 1, 1, tzinfo=UTC),
            referencia_documento="ACTA-BASE",
            justificacion="Escenario ficticio en base aislada",
        )
    )
    db.add_all(
        [
            Existencia(activo_id=a.id, area_id=origen.id, cantidad=30, estado="activo"),
            Existencia(activo_id=a.id, area_id=destino.id, cantidad=42, estado="activo"),
        ]
    )
    for area, cantidad in ((origen, 60), (destino, 20)):
        db.add(
            AuditoriaSistema(
                usuario_id=u.id,
                accion="asignar_existencia_area",
                recurso="existencia",
                recurso_id=a.id,
                resultado="exito",
                fecha_hora=datetime(2026, 1, 2, tzinfo=UTC),
                detalle={"area_id": area.id, "cantidad": cantidad},
            )
        )
    db.add(
        TransferenciaArea(
            solicitud_id=str(uuid4()),
            solicitud_huella="a" * 64,
            articulo_id=a.id,
            area_origen_id=origen.id,
            area_destino_id=destino.id,
            cantidad=10,
            total_institucional=100,
            encargado_id=u.id,
            registrado_por=u.id,
            ocurrido_en=datetime(2027, 1, 2, tzinfo=UTC),
            registrado_en=datetime(2027, 1, 2, tzinfo=UTC),
            referencia_documento="TRASLADO-QA",
        )
    )
    c = CustodiaExterna(
        solicitud_id=str(uuid4()),
        solicitud_huella="b" * 64,
        articulo_id=a.id,
        area_origen_id=origen.id,
        tipo="FERIA",
        receptor_nombre="Receptor QA",
        receptor_tipo="INSTITUCION",
        ubicacion_externa="Feria QA",
        cantidad_entregada=20,
        cantidad_fuera=10,
        cantidad_vendida=5,
        cantidad_devuelta=5,
        total_institucional_entrega=100,
        encargado_id=u.id,
        registrado_por=u.id,
        ocurrido_en=datetime(2027, 1, 3, tzinfo=UTC),
        registrado_en=datetime(2027, 1, 3, tzinfo=UTC),
        referencia_documento="FERIA-QA",
    )
    db.add(c)
    db.flush()
    for i, tipo in enumerate(("VENTA", "RETORNO")):
        db.add(
            EventoCustodiaExterna(
                solicitud_id=str(uuid4()),
                solicitud_huella=str(i) * 64,
                articulo_id=a.id,
                custodia_id=c.id,
                tipo=tipo,
                cantidad=5,
                area_destino_id=destino.id if tipo == "RETORNO" else None,
                encargado_id=u.id,
                registrado_por=u.id,
                ocurrido_en=datetime(2027, 1, 4 + i, tzinfo=UTC),
                registrado_en=datetime(2027, 1, 4 + i, tzinfo=UTC),
                referencia_documento="EVENTO-QA",
                total_institucional_despues=95,
                cantidad_fuera_despues=15 if tipo == "VENTA" else 10,
            )
        )
    db.add(
        MovimientoKardex(
            articulo_id=a.id,
            fecha_movimiento=datetime(2027, 1, 6).date(),
            detalle="Ingreso posterior al año cerrado",
            ingresos=7,
            saldo_registrado=102,
            registrado_en=datetime(2027, 1, 6, tzinfo=UTC),
            ocurrido_en=datetime(2027, 1, 6, tzinfo=UTC),
            encargado_id=u.id,
            tipo_operacion="Inventario / Compra",
            area_operativa_id=destino.id,
        )
    )
    db.commit()
    return a, origen, destino


def test_reconstruye_antes_de_transferencias_custodia_e_ingresos(escenario, db_session):
    a, origen, destino = escenario
    p = servicio.reconstruir(db_session, 2026)
    assert p["puede_cerrar"], p["impedimentos"]
    fila = p["snapshot"]["articulos"][0]
    assert (fila["total"], fila["sin_ubicacion"], fila["custodia"]) == (100, 20, 0)
    assert fila["areas"] == [
        {"area_id": origen.id, "cantidad": 60},
        {"area_id": destino.id, "cantidad": 20},
    ]
    assert db_session.get(AperturaInventario, a.id).cantidad_actual == 102


def test_cierre_reintento_reapertura_y_nueva_version_no_mueven_stock(
    escenario, usuario_admin, usuario_operador, db_session, client
):
    h = cabecera(usuario_admin)
    p = client.get("/api/v1/cierres-anuales/2026/vista-previa", headers=h).json()
    body = {
        "solicitud_id": str(uuid4()),
        "huella_esperada": p["huella"],
        "documento": "ACTA-CIERRE-QA",
        "motivo": "Cierre digital únicamente en entorno ficticio de prueba",
        "balance_revisado": True,
    }
    assert (
        client.post(
            "/api/v1/cierres-anuales/2026", json=body, headers=cabecera(usuario_operador)
        ).status_code
        == 403
    )
    r = client.post("/api/v1/cierres-anuales/2026", json=body, headers=h)
    assert r.status_code == 201, r.text
    c = db_session.get(CierreAnual, r.json()["id"])
    snapshot = deepcopy(c.snapshot)
    assert client.post("/api/v1/cierres-anuales/2026", json=body, headers=h).json()["id"] == c.id
    assert db_session.query(CierreAnual).count() == 1
    assert (
        client.post(
            f"/api/v1/cierres-anuales/registro/{c.id}/reabrir",
            headers=h,
            json={"motivo": "Revisar un documento adicional de la prueba"},
        ).status_code
        == 200
    )
    assert c.snapshot == snapshot
    body["solicitud_id"] = str(uuid4())
    assert client.post("/api/v1/cierres-anuales/2026", json=body, headers=h).json()["version"] == 2
    assert db_session.get(AperturaInventario, escenario[0].id).cantidad_actual == 102


def test_rechaza_corte_cambiado_y_ano_no_concluido(escenario, usuario_admin, client, monkeypatch):
    h = cabecera(usuario_admin)
    b = {
        "solicitud_id": str(uuid4()),
        "huella_esperada": "0" * 64,
        "documento": "ACTA-CIERRE-QA",
        "motivo": "Balance de prueba todavía no confirmado",
        "balance_revisado": True,
    }
    assert client.post("/api/v1/cierres-anuales/2026", json=b, headers=h).status_code == 409
    monkeypatch.setattr(servicio, "ahora", lambda: datetime(2026, 12, 1, tzinfo=UTC))
    assert not client.get("/api/v1/cierres-anuales/2026/vista-previa", headers=h).json()[
        "puede_cerrar"
    ]


def test_cierre_bloquea_saldo_frente_a_otra_conexion(
    escenario, usuario_admin, db_session, client, monkeypatch
):
    motor = db_session.get_bind()
    if motor.dialect.name != "postgresql":
        pytest.skip("La concurrencia exige PostgreSQL real")
    h = cabecera(usuario_admin)
    preview = servicio.reconstruir(db_session, 2026)
    reconstruir_original = servicio.reconstruir
    comprobaciones = []

    def reconstruir_protegido(db, gestion):
        # Simula el bloqueo usado por transferencias/custodias, desde otra sesión.
        with motor.connect() as otra:
            otra.execute(text("SET LOCAL lock_timeout = '250ms'"))
            with pytest.raises(OperationalError) as error:
                otra.execute(
                    text(
                        "SELECT articulo_id FROM apertura_inventario "
                        "WHERE articulo_id = :id FOR UPDATE"
                    ),
                    {"id": escenario[0].id},
                )
            assert error.value.orig.pgcode == "55P03"
            otra.rollback()
        comprobaciones.append(True)
        return reconstruir_original(db, gestion)

    monkeypatch.setattr(servicio, "reconstruir", reconstruir_protegido)
    respuesta = client.post(
        "/api/v1/cierres-anuales/2026",
        headers=h,
        json={
            "solicitud_id": str(uuid4()),
            "huella_esperada": preview["huella"],
            "documento": "CIERRE-QA",
            "motivo": "Verificación de concurrencia aislada",
            "balance_revisado": True,
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    assert comprobaciones == [True]
