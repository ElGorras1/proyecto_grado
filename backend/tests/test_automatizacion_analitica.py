"""Automatización con artefactos QA reales y conservación de cortes, datos y revisiones."""

# ruff: noqa: F811 -- pytest inyecta la fixture historico importada por nombre.
from datetime import UTC, datetime, timedelta, date
from copy import deepcopy
import hashlib
import pytest
from app.models.activos import Activo
from app.models.auditoria_historica import ModeloHistorico, ResultadoHistorico
from app.models.automatizacion_analitica import PoliticaAnalitica, ResultadoSeguimiento
from app.models.kardex import MovimientoKardex, LoteCarga
from app.services import automatizacion_analitica as servicio
from app.services.datos_analitica import leer_corte, huella
from app.services.trabajador_analitica import ejecutar
from app.services.tratamiento_hil import huella_datos
from test_analitica import historico, trabajo, cabecera  # noqa: F401

T = datetime(2026, 10, 31, 20, tzinfo=UTC)


@pytest.fixture
def preparado(db_session, usuario_admin, historico, tmp_path, monkeypatch):
    m = trabajo(db_session, usuario_admin)
    ejecutar(db_session, m.id, tmp_path)
    assert m.estado == "COMPLETADO", m.error
    monkeypatch.setattr(servicio, "ARTEFACTOS", tmp_path)
    p = PoliticaAnalitica(
        id=1,
        modelo_base_id=m.id,
        habilitada=True,
        preparar_candidatos=True,
        gestion_hasta=2025,
        intervalo_segundos=300,
        revision_dias=30,
        ultima_revision=T,
        huella_revision=servicio.huella_entrenamiento(servicio.elegibles_del_corte(m.corte, 2025)),
    )
    db_session.add(p)
    db_session.commit()
    return m, p, tmp_path


def cambiar(db):
    f = db.query(MovimientoKardex).order_by(MovimientoKardex.id).first()
    f.salidas = 900
    f.detalle = "Cantidad cotejada en evidencia QA"
    db.commit()
    return f


def test_no_reentrena_si_el_archivo_es_el_mismo(db_session, preparado):
    m, p, ruta = preparado
    p.ultima_revision = T - timedelta(days=31)
    db_session.commit()
    original = huella(m.corte)
    r = servicio.ejecutar_ciclo(db_session, instante=T)
    assert r["nuevos_resultados"] == 0 and r["mantenimiento"]["estado"] == "SIN_CAMBIOS"
    assert db_session.query(ModeloHistorico).count() == 1
    assert db_session.query(ResultadoSeguimiento).count() == 0
    assert huella(m.corte) == original


def test_inferencia_idempotente_conserva_pesos_corte_y_fuentes(db_session, preparado):
    m, p, ruta = preparado
    digest = hashlib.sha256((ruta / (m.id + ".joblib")).read_bytes()).hexdigest()
    corte = deepcopy(m.corte)
    resultados = [
        (r.id, r.score, r.snapshot)
        for r in db_session.query(ResultadoHistorico).order_by(ResultadoHistorico.id)
    ]
    f = cambiar(db_session)
    datos = huella(leer_corte(db_session)["filas"])
    resumen = servicio.ejecutar_ciclo(db_session, instante=T)
    assert resumen["nuevos_resultados"] == 1
    nuevo = db_session.query(ResultadoSeguimiento).one()
    assert (
        nuevo.movimiento_id == f.id and nuevo.snapshot["salidas"] == 900 and nuevo.modelo_id == m.id
    )
    assert (
        servicio.ejecutar_ciclo(db_session, instante=T + timedelta(minutes=6))["nuevos_resultados"]
        == 0
    )
    assert (
        db_session.query(ResultadoSeguimiento).count() == 1
        and db_session.query(ModeloHistorico).count() == 1
    )
    assert huella(leer_corte(db_session)["filas"]) == datos
    assert (
        m.corte == corte
        and hashlib.sha256((ruta / (m.id + ".joblib")).read_bytes()).hexdigest() == digest
    )
    assert [
        (r.id, r.score, r.snapshot)
        for r in db_session.query(ResultadoHistorico).order_by(ResultadoHistorico.id)
    ] == resultados


def test_respeta_intervalo_y_reintenta_tras_reiniciar(db_session, preparado, monkeypatch):
    servicio.ejecutar_ciclo(db_session, instante=T)
    original = servicio.leer_corte
    veces = []

    def leer(db):
        veces.append(1)
        return original(db)

    monkeypatch.setattr(servicio, "leer_corte", leer)
    assert servicio.ejecutar_ciclo(db_session, instante=T + timedelta(seconds=299)) is None
    assert veces == []
    servicio.ejecutar_ciclo(db_session, instante=T + timedelta(minutes=10))
    assert veces == [1]


def test_excluye_fechas_ajenas_al_alcance_y_casos_hil(db_session, preparado):
    cambiar(db_session)
    filas = db_session.query(MovimientoKardex).order_by(MovimientoKardex.id).limit(2).all()
    filas[0].fecha_movimiento = date(2026, 1, 1)
    filas[1].tiene_error_saldo = True
    db_session.commit()
    r = servicio.ejecutar_ciclo(db_session, instante=T)
    assert r["elegibles"] == 198 and r["nuevos_resultados"] == 0


def test_artefacto_alterado_no_publica_resultados_y_registra_error(db_session, preparado):
    m, p, ruta = preparado
    cambiar(db_session)
    (ruta / (m.id + ".joblib")).write_bytes(b"artefacto QA alterado")
    assert servicio.ejecutar_ciclo(db_session, instante=T) is None
    assert db_session.query(ResultadoSeguimiento).count() == 0
    db_session.refresh(p)
    assert p.ultimo_error and p.modelo_base_id == m.id
    assert db_session.query(ResultadoHistorico).count() == 200


def test_cambios_insuficientes_no_generan_trabajos_inutiles(db_session, preparado):
    m, p, ruta = preparado
    cambiar(db_session)
    p.ultima_revision = T - timedelta(days=31)
    db_session.commit()
    r = servicio.ejecutar_ciclo(db_session, instante=T)
    assert r["mantenimiento"]["estado"] == "MUESTRA_INSUFICIENTE"
    assert p.modelo_base_id == m.id and db_session.query(ModeloHistorico).count() == 1


def test_prepara_candidato_periodico_sin_activar_ni_sustituir(db_session, preparado, historico):
    m, p, ruta = preparado
    for j in range(4):
        art = Activo(
            categoria_id=historico.categoria_id,
            nombre=f"Catálogo independiente {j}",
            codigo=f"N{j}",
        )
        lote = LoteCarga(total_imagenes=1)
        db_session.add_all([art, lote])
        db_session.flush()
        for i in range(70):
            db_session.add(
                MovimientoKardex(
                    articulo_id=art.id,
                    lote_id=lote.id,
                    fecha_movimiento=date(2022, 1, 1),
                    detalle="Fila QA",
                    salidas=i % 7 + 1,
                    saldo_registrado=1000 - i,
                    numero_pagina=1,
                    orden_fila=i + 1,
                    nodo_grafo="Ventas",
                    ruta_imagen_respaldo=f"storage/qa-{j}.png",
                    estado="ACTIVO",
                    fecha_estado="SIN_ALERTA",
                    area_estado="RESUELTA_AUTOMATICAMENTE",
                    referencia_estado="AUSENTE",
                    requiere_auditoria_nodo=False,
                    requiere_auditoria_referencia=False,
                    tiene_error_saldo=False,
                    tiene_error_fecha=False,
                )
            )
    p.ultima_revision = T - timedelta(days=31)
    db_session.commit()
    r = servicio.ejecutar_ciclo(db_session, instante=T)
    assert r["mantenimiento"]["estado"] == "CANDIDATO_PREPARADO"
    candidato = db_session.get(ModeloHistorico, p.candidato_id)
    assert candidato.estado == "PENDIENTE" and candidato.configuracion["modo"] == "POR_ARTICULO"
    assert candidato.configuracion["candidato_automatico"] is True
    assert p.modelo_base_id == m.id and servicio.modelo_referencia(db_session).id == m.id
    servicio.ejecutar_ciclo(db_session, instante=T + timedelta(minutes=10))
    assert db_session.query(ModeloHistorico).count() == 2


def test_revision_controla_roles_version_y_evidencia(
    client, db_session, preparado, usuario_admin, usuario_operador
):
    cambiar(db_session)
    servicio.ejecutar_ciclo(db_session, instante=T)
    r = db_session.query(ResultadoSeguimiento).one()
    url = f"/api/v1/automatizacion/seguimiento/{r.id}/revision"
    payload = dict(
        estado="EN_REVISION",
        etiqueta="NO_CONCLUYENTE",
        motivo="Cotejo independiente de la foto QA",
        revision_esperada=0,
    )
    assert client.post(url, json=payload).status_code == 401
    assert client.post(url, json=payload, headers=cabecera(usuario_operador)).status_code == 403
    assert client.post(url, json=payload, headers=cabecera(usuario_admin)).status_code == 200
    assert client.post(url, json=payload, headers=cabecera(usuario_admin)).status_code == 409
    f = db_session.get(MovimientoKardex, r.movimiento_id)
    f.tiene_error_saldo = True
    db_session.commit()
    assert (
        client.post(
            url, json={**payload, "revision_esperada": 1}, headers=cabecera(usuario_admin)
        ).status_code
        == 409
    )


def test_politica_solo_admin_y_detecta_cambios_concurrentes(
    client, db_session, preparado, usuario_admin, usuario_operador
):
    m, p, ruta = preparado
    url = "/api/v1/automatizacion/politica"
    h = cabecera(usuario_admin)
    estado = client.get("/api/v1/automatizacion/estado", headers=h).json()
    payload = dict(
        modelo_base_id=m.id,
        revision_dias=20,
        motivo="Ajustar la revisión periódica de QA",
        huella_esperada=estado["huella_politica"],
    )
    assert client.put(url, json=payload, headers=cabecera(usuario_operador)).status_code == 403
    respuesta = client.put(url, json=payload, headers=h)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["revision_dias"] == 20
    assert client.put(url, json=payload, headers=h).status_code == 409


def test_bandeja_no_repite_categorizaciones_ni_confunde_origen(
    client, db_session, preparado, usuario_admin
):
    m, p, ruta = preparado
    fila = db_session.query(MovimientoKardex).order_by(MovimientoKardex.id).first()
    fila.tiene_error_saldo = True
    db_session.commit()
    fila.revision_documental = {
        "tratamiento_hil": {
            "version": 1,
            "huella_datos": huella_datos(fila),
            "avisos": ["saldo"],
            "decisiones": [
                {
                    "campo": "saldo",
                    "categoria": "DISCREPANCIA_DOCUMENTAL",
                    "motivo": "Diferencia documental conservada",
                    "criterios": ["T05"],
                }
            ],
        }
    }
    db_session.commit()
    url = "/api/v1/revisiones/pendientes"
    assert client.get(url).status_code == 401
    h = cabecera(usuario_admin)
    assert client.get(url, headers=h, params={"origen": "HIL"}).json()["total"] == 0
    datos = client.get(url, headers=h, params={"origen": "HIL", "incluir_tratados": True}).json()
    assert datos["total"] == 1 and datos["filas"][0]["destino"]["query"]["tab"] == "hil"
    assert datos["filas"][0]["estado"] == "Categorizado con marca"
    assert (
        client.get(url, headers=h, params={"gestion": 2020, "sin_fecha": True}).status_code == 422
    )


def test_bandeja_muestra_solo_seguimiento_vigente_y_enlaza_el_corte(
    client, db_session, preparado, usuario_admin
):
    m, p, ruta = preparado
    f = cambiar(db_session)
    servicio.ejecutar_ciclo(db_session, instante=T)
    nuevo = db_session.query(ResultadoSeguimiento).one()
    nuevo.alerta = True
    viejo = db_session.query(ResultadoHistorico).filter_by(modelo_id=m.id, movimiento_id=f.id).one()
    viejo.alerta = True
    db_session.commit()
    h = cabecera(usuario_admin)
    datos = client.get(
        "/api/v1/revisiones/pendientes", headers=h, params={"origen": "MODELO", "limite": 100}
    ).json()
    assert any(v["tipo"] == "SEGUIMIENTO" and v["id"] == nuevo.id for v in datos["filas"])
    assert not any(v["tipo"] == "HISTORICO" and v["id"] == viejo.id for v in datos["filas"])
    f.detalle = "Nueva corrección documental QA"
    db_session.commit()
    datos = client.get(
        "/api/v1/revisiones/pendientes", headers=h, params={"origen": "MODELO", "limite": 100}
    ).json()
    assert not any(v["tipo"] == "SEGUIMIENTO" and v["id"] == nuevo.id for v in datos["filas"])
    anterior = next(v for v in datos["filas"] if v["tipo"] == "HISTORICO" and v["id"] == viejo.id)
    assert (
        anterior["destino"]["query"]["modelo"] == m.id
        and anterior["destino"]["query"]["resultado_id"] == viejo.id
    )


def test_reactivar_revisa_datos_pendientes_sin_entrenar_desde_el_formulario(
    client, db_session, preparado, usuario_admin
):
    m, p, ruta = preparado
    p.habilitada = False
    p.preparar_candidatos = False
    p.ultimo_analisis = T
    p.huella_revision = "0" * 64
    db_session.commit()
    h = cabecera(usuario_admin)
    e = client.get("/api/v1/automatizacion/estado", headers=h).json()
    r = client.put(
        "/api/v1/automatizacion/politica",
        headers=h,
        json=dict(
            modelo_base_id=m.id,
            habilitada=True,
            preparar_candidatos=True,
            huella_esperada=e["huella_politica"],
            motivo="Reanudar comprobaciones pendientes de QA",
        ),
    )
    assert r.status_code == 200, r.text
    db_session.refresh(p)
    assert p.ultimo_analisis is None and p.ultima_revision is None
    assert p.huella_revision == servicio.huella_entrenamiento(
        servicio.elegibles_del_corte(m.corte, 2025)
    )
    assert db_session.query(ModeloHistorico).count() == 1
