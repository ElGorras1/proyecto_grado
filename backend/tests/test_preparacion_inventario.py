from datetime import UTC, datetime
from zoneinfo import ZoneInfo
import pytest
from app.models.activos import Existencia
from app.models.area import Area
from app.models.cierre_anual import CierreAnual
from app.models.inventario import AperturaInventario, TransferenciaArea
from app.services.preparacion_inventario import preparar
from app.services import cierre_anual
from test_kardex import activos_prueba, auth_headers, usuario_auditor
from test_transferencias_area import escenario


def test_preparacion_distingue_fuente_conteo_y_ubicacion(db_session, usuario_admin, activos_prueba):
    a, b = activos_prueba
    db_session.add(AperturaInventario(articulo_id=a.id, cantidad_inicial=20, cantidad_actual=20,
        cantidad_sin_ubicacion=20, cantidad_custodia_externa=0, ultimo_moderno_id=0, aprobado_por=usuario_admin.id,
        aprobado_en=datetime.now(UTC), referencia_documento="ACTA-QA", justificacion="Conteo registrado en fixture QA",
        origen="CONTEO_FISICO"))
    db_session.add(Area(nombre="Galería", estado="activo")); db_session.commit()
    antes = db_session.query(Existencia).count()
    datos = preparar(db_session)
    assert datos["resumen"]["unidades_sin_ubicacion"] == 20
    assert datos["resumen"]["articulos_con_unidades_sin_ubicacion"] == 1
    assert not datos["transferencias_entre_areas_disponibles"]
    fila = next(f for f in datos["articulos"] if f["articulo_id"] == a.id)
    assert fila["pendientes"] == ["UBICACION_PENDIENTE"] and fila["conteo_aprobado"]
    assert fila["saldo_operativo"] == 20 and fila["integridad"]
    assert next(f for f in datos["articulos"] if f["articulo_id"] == b.id)["pendientes"] == ["SIN_BASE"]
    assert db_session.query(Existencia).count() == antes


def test_preparacion_no_declara_integridad_si_hay_diferencia(db_session, usuario_admin, activos_prueba):
    a, _ = activos_prueba
    db_session.add(AperturaInventario(articulo_id=a.id, cantidad_inicial=10, cantidad_actual=10,
        cantidad_sin_ubicacion=9, cantidad_custodia_externa=0, ultimo_moderno_id=0, aprobado_por=usuario_admin.id,
        aprobado_en=datetime.now(UTC), referencia_documento="QA", justificacion="Diferencia simulada", origen="CONTEO_FISICO"))
    db_session.commit()
    fila = preparar(db_session)["articulos"][0]
    assert not fila["integridad"] and fila["prioridad"] == 0 and "INTEGRIDAD_PENDIENTE" in fila["pendientes"]


def test_indicios_de_prueba_no_confunden_testimonios_ni_eliminan_stock(db_session, usuario_admin, activos_prueba):
    a, b = activos_prueba
    a.nombre = "PRUEBA E91159"
    b.nombre = "TESTIMONIOS DE LA LITERATURA BOLIVIANA VOL. 2"
    for articulo, cantidad in ((a, 20), (b, 6)):
        db_session.add(AperturaInventario(articulo_id=articulo.id, cantidad_inicial=cantidad, cantidad_actual=cantidad,
            cantidad_sin_ubicacion=cantidad, cantidad_custodia_externa=0, ultimo_moderno_id=0, aprobado_por=usuario_admin.id,
            aprobado_en=datetime.now(UTC), referencia_documento="ACTA-QA", justificacion="Perfil sintético para revisión de indicios.",
            origen="CONTEO_FISICO"))
    db_session.commit()
    datos = preparar(db_session)
    assert datos["resumen"]["unidades_sin_ubicacion"] == 26
    assert datos["resumen"]["unidades_sin_ubicacion_con_indicio_prueba"] == 20
    assert datos["resumen"]["unidades_sin_ubicacion_sin_indicio_prueba"] == 6
    assert next(f for f in datos["articulos"] if f["articulo_id"] == a.id)["indicio_prueba"]
    assert not next(f for f in datos["articulos"] if f["articulo_id"] == b.id)["indicio_prueba"]
    assert db_session.get(AperturaInventario, a.id).cantidad_actual == 20


@pytest.mark.parametrize("rol", ["admin", "operador", "auditor"])
def test_preparacion_es_consulta_autenticada(client, usuario_admin, usuario_operador, usuario_auditor, rol):
    assert client.get("/api/v1/inventario/preparacion").status_code == 401
    usuario = {"admin": usuario_admin, "operador": usuario_operador, "auditor": usuario_auditor}[rol]
    r = client.get("/api/v1/inventario/preparacion", headers=auth_headers(usuario))
    assert r.status_code == 200 and "articulos" in r.json()


def test_conciliacion_inicial_no_borra_efectos_de_transferencia(client, db_session, usuario_admin, activos_prueba):
    a, _ = activos_prueba
    origen, destino = escenario(client, db_session, usuario_admin, a)
    from uuid import uuid4
    r = client.post(f"/api/v1/kardex/articulos/{a.id}/transferencias", headers=auth_headers(usuario_admin), json={
        "solicitud_id": str(uuid4()), "area_origen_id": origen.id, "area_destino_id": destino.id,
        "cantidad": 1, "encargado_id": usuario_admin.id, "referencia_documento": "ACTA-TR-QA"})
    assert r.status_code == 200
    ruta = f"/api/v1/kardex/articulos/{a.id}/conciliacion-inicial"
    antes = {e.area_id: e.cantidad for e in db_session.query(Existencia).filter_by(activo_id=a.id)}
    estado = client.get(ruta, headers=auth_headers(usuario_admin)).json()
    assert estado["estado"] == "NO_DISPONIBLE" and "transferencias" in estado["motivo"]
    r = client.post(ruta, headers=auth_headers(usuario_admin), json={
        "fecha_conteo": str(datetime.now(ZoneInfo("America/La_Paz")).date()), "areas": [{"area_id": origen.id, "cantidad": 10}],
        "encargado_id": usuario_admin.id, "referencia_documento": "ACTA-CONTEO-QA",
        "justificacion": "No debe reemplazar las ubicaciones posteriores", "alcance_total": True, "conteo_verificado": True})
    assert r.status_code == 409
    assert {e.area_id: e.cantidad for e in db_session.query(Existencia).filter_by(activo_id=a.id)} == antes


def test_apertura_fisica_respeta_periodo_cerrado(client, db_session, usuario_admin, activos_prueba):
    from uuid import uuid4
    a, _ = activos_prueba
    gestion = cierre_anual.ahora().year
    db_session.add(CierreAnual(solicitud_id=str(uuid4()), solicitud_huella="a"*64,
        gestion=gestion, gestion_activa=gestion, version=1, estado="CERRADO", snapshot={},
        huella="b"*64, usuario_id=usuario_admin.id, creado_en=datetime.now(UTC), documento="CIERRE-QA",
        motivo="Escenario de cierre en base aislada"))
    db_session.commit()
    r = client.post(f"/api/v1/kardex/articulos/{a.id}/apertura", headers=auth_headers(usuario_admin),
        json={"cantidad": 10, "referencia_documento": "ACTA-QA", "justificacion": "Conteo simulado en año cerrado", "conteo_verificado": True})
    assert r.status_code == 409 and db_session.get(AperturaInventario, a.id) is None
