from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token
from app.models.activos import Activo, CategoriaActivo
from app.models.auditoria import AuditoriaSistema
from app.models.auditoria_historica import ModeloHistorico, ResultadoHistorico, RevisionHistorica
from app.models.kardex import LoteCarga, MovimientoKardex
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.schemas.analitica import EntrenamientoHistorico
from app.services.datos_analitica import huella, leer_corte, seleccionar
from app.services.isolation_historico import Contexto, calcular, particionar
from app.services.trabajador_analitica import ejecutar, recuperar_interrumpidos


def cabecera(u):
    return {"Authorization": "Bearer " + create_access_token(subject=u.id)}


@pytest.fixture
def historico(db_session):
    db = db_session
    categoria = CategoriaActivo(nombre="Catálogo", estado="activo")
    db.add(categoria)
    db.flush()
    a = Activo(categoria_id=categoria.id, nombre="Historia institucional", codigo="HIS-1")
    db.add(a)
    db.flush()
    for lote in range(10):
        lote_carga = LoteCarga(total_imagenes=1)
        db.add(lote_carga)
        db.flush()
        for i in range(20):
            db.add(
                MovimientoKardex(
                    articulo_id=a.id,
                    lote_id=lote_carga.id,
                    fecha_movimiento=date(2020 + lote % 3, 1, i + 1),
                    detalle=f"Documento {lote}-{i}",
                    ingresos=None,
                    salidas=(i % 7) + 1,
                    saldo_registrado=1000 - i,
                    numero_pagina=1,
                    orden_fila=i + 1,
                    nodo_grafo="Biblioteca" if i % 3 else "Ventas",
                    ruta_imagen_respaldo="storage/kardex_images/evidencia.webp",
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
    db.commit()
    return a


def trabajo(db, usuario):
    corte = leer_corte(db)
    j = ModeloHistorico(
        id=str(uuid4()),
        usuario_id=usuario.id,
        estado="PENDIENTE",
        plaza=1,
        configuracion=EntrenamientoHistorico(arboles=100).model_dump(),
        corte=corte,
        huella=huella(corte["filas"]),
    )
    db.add(j)
    db.commit()
    return j


def test_elegibilidad_y_cobertura(historico, db_session):
    filas = leer_corte(db_session)["filas"]
    casos = [
        {"estado": "ANULADO"},
        {"lote_id": None},
        {"alertas_hil": ["fecha"]},
        {"ingresos": 5, "salidas": 2},
        {"ingresos": None, "salidas": None},
        {"salidas": -1},
        {"ruta_imagen_respaldo": None},
        {"articulo": "Artículo de prueba"},
    ]
    for i, cambio in enumerate(casos):
        filas[i].update(cambio)
    elegibles, excluidas = seleccionar(filas)
    assert len(elegibles) == 192
    assert sum(map(len, excluidas.values())) == 8
    # Ausencia documental confirmada sí puede participar.
    filas[10]["nodo_grafo"] = "Destino no especificado"
    assert filas[10] in seleccionar(filas)[0]
    assert not seleccionar(filas, [historico.id])[0]


def test_particiones_sin_fuga_y_reproducibles(historico, db_session):
    filas = leer_corte(db_session)["filas"]
    partes = particionar(filas, 42)
    por_lote = {}
    for f, p in zip(filas, partes):
        assert por_lote.setdefault(f["lote_id"], p) == p
    assert partes == particionar(filas, 42)
    config = EntrenamientoHistorico(arboles=100).model_dump()
    a = calcular(filas, config)
    b = calcular(filas, config)
    assert a[2:] == b[2:]
    assert a[3]["precision_at_k"] is None
    train = [f for f, p in zip(filas, partes) if p == "entrenamiento"]
    c = Contexto().fit(train)
    desconocido = {**filas[0], "articulo_id": 9999, "nodo_grafo": "Nuevo"}
    antes = dict(c.estadisticas)
    x, contexto = c.transformar([desconocido])
    assert contexto[0]["referencias"] == 0
    assert c.estadisticas == antes
    assert x.shape == (1, 7)


def test_duplicados_se_agrupan(historico, db_session):
    filas = leer_corte(db_session)["filas"]
    campos = (
        "articulo_id",
        "fecha",
        "detalle",
        "referencia",
        "area",
        "ingresos",
        "salidas",
        "saldo_registrado",
    )
    for k in campos:
        filas[20][k] = filas[0][k]
    partes = particionar(filas, 42)
    assert partes[0] == partes[20]


def test_entrenamiento_persistencia_conservacion_y_cambios(
    client, historico, usuario_admin, db_session, tmp_path
):
    db = db_session
    antes = leer_corte(db)["filas"]
    j = trabajo(db, usuario_admin)
    ejecutar(db, j.id, tmp_path)
    assert j.estado == "COMPLETADO"
    assert j.plaza is None
    assert (tmp_path / (j.id + ".joblib")).exists()
    assert leer_corte(db)["filas"] == antes
    assert db.query(ResultadoHistorico).count() == 200
    ejecutar(db, j.id, tmp_path)
    assert db.query(ResultadoHistorico).count() == 200
    h = cabecera(usuario_admin)
    response = client.get(
        "/api/v1/analitica/resultados",
        headers=h,
        params={"modelo_id": j.id, "gestion": 2020, "limite": 3},
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["filas"]) == 3
    assert response.json()["total"] == 80
    r = db.query(ResultadoHistorico).first()
    db.get(MovimientoKardex, r.movimiento_id).salidas = 999
    db.commit()
    detail = client.get(f"/api/v1/analitica/resultados/{r.id}", headers=h).json()
    assert detail["datos_cambiaron"]
    assert detail["snapshot"]["salidas"] != 999
    assert client.get(f"/api/v1/analitica/modelos/{j.id}", headers=h).json()["datos_cambiaron"]


def test_revision_permisos_conflicto_y_auditoria(
    client, historico, usuario_admin, usuario_operador, db_session, tmp_path
):
    db = db_session
    j = trabajo(db, usuario_admin)
    ejecutar(db, j.id, tmp_path)
    r = db.query(ResultadoHistorico).first()
    url = f"/api/v1/analitica/resultados/{r.id}/revision"
    payload = {
        "estado": "JUSTIFICADO",
        "etiqueta": "LEGITIMO",
        "motivo": "Contrastado con el documento institucional.",
        "revision_esperada": 0,
    }
    assert client.post(url, headers=cabecera(usuario_operador), json=payload).status_code == 403
    assert client.post(url, headers=cabecera(usuario_admin), json=payload).status_code == 200
    assert client.post(url, headers=cabecera(usuario_admin), json=payload).status_code == 409
    assert db.query(RevisionHistorica).count() == 1
    assert db.query(AuditoriaSistema).filter_by(accion="ANALITICA_REVISADA").count() == 1
    payload["revision_esperada"] = 1
    payload["motivo"] = " " * 20
    assert client.post(url, headers=cabecera(usuario_admin), json=payload).status_code == 422
    rol = Rol(nombre="Auditor", estado="activo")
    db.add(rol)
    db.flush()
    u = Usuario(
        rol_id=rol.id,
        nombre="Auditor",
        email="auditoria@local.test",
        password_hash="unused",
        estado="activo",
    )
    db.add(u)
    db.commit()
    payload["motivo"] = "Revisión adicional del documento."
    assert client.post(url, headers=cabecera(u), json=payload).status_code == 200
    assert (
        client.post("/api/v1/analitica/entrenar", headers=cabecera(u), json={}).status_code == 403
    )


def test_trabajo_insuficiente_fallo_y_recuperacion(
    historico, usuario_admin, db_session, tmp_path, monkeypatch
):
    db = db_session
    j = trabajo(db, usuario_admin)
    j.corte = {**j.corte, "filas": j.corte["filas"][:10]}
    db.commit()
    ejecutar(db, j.id, tmp_path)
    assert j.estado == "INSUFICIENTE" and j.plaza is None
    j2 = trabajo(db, usuario_admin)
    import joblib

    def fallar(*args, **kwargs):
        raise OSError("disco")

    monkeypatch.setattr(joblib, "dump", fallar)
    ejecutar(db, j2.id, tmp_path)
    assert j2.estado == "FALLIDO" and j2.plaza is None
    assert db.query(ResultadoHistorico).count() == 0
    j3 = trabajo(db, usuario_admin)
    j3.estado = "EN_EJECUCION"
    db.commit()
    recuperar_interrumpidos(db)
    assert j3.estado == "FALLIDO" and j3.plaza is None


def test_api_entrenamiento_unico_y_autenticacion(
    client, historico, usuario_admin, usuario_operador, db_session
):
    assert client.get("/api/v1/analitica/perfil").status_code == 401
    assert client.post("/api/v1/analitica/entrenar", json={}).status_code == 401
    assert (
        client.post(
            "/api/v1/analitica/entrenar", headers=cabecera(usuario_operador), json={}
        ).status_code
        == 403
    )
    h = cabecera(usuario_admin)
    assert (
        client.post(
            "/api/v1/analitica/entrenar", headers=h, json={"porcentaje_revision": 90}
        ).status_code
        == 422
    )
    r = client.post("/api/v1/analitica/entrenar", headers=h, json={})
    assert r.status_code == 202, r.text
    assert client.post("/api/v1/analitica/entrenar", headers=h, json={}).status_code == 409
    j = db_session.get(ModeloHistorico, r.json()["job_id"])
    j2 = ModeloHistorico(
        id=str(uuid4()),
        usuario_id=usuario_admin.id,
        estado="PENDIENTE",
        plaza=1,
        configuracion=j.configuracion,
        corte=j.corte,
        huella=j.huella,
    )
    db_session.add(j2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_precision_exige_revision_completa(client, historico, usuario_admin, db_session, tmp_path):
    j = trabajo(db_session, usuario_admin)
    ejecutar(db_session, j.id, tmp_path)
    url = f"/api/v1/analitica/modelos/{j.id}/evaluacion"
    h = cabecera(usuario_admin)
    assert client.get(url, headers=h).json()["modelo"]["precision_at_k"] is None
    for r in db_session.query(ResultadoHistorico).filter(
        ResultadoHistorico.movimiento_id.in_(j.metricas["top_evaluacion"])
    ):
        r.estado_revision = "CERRADO"
        r.etiqueta = "INUSUAL_RELEVANTE"
    db_session.commit()
    assert client.get(url, headers=h).json()["modelo"]["precision_at_k"] == 1.0


def test_revision_y_auditoria_atomicas(
    client, historico, usuario_admin, db_session, tmp_path, monkeypatch
):
    j = trabajo(db_session, usuario_admin)
    ejecutar(db_session, j.id, tmp_path)
    r = db_session.query(ResultadoHistorico).first()
    from app.api.v1.endpoints import analitica

    def falla_auditoria(*args, **kwargs):
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr(analitica, "evento", falla_auditoria)
    with pytest.raises(RuntimeError, match="fallo simulado"):
        client.post(
            f"/api/v1/analitica/resultados/{r.id}/revision",
            headers=cabecera(usuario_admin),
            json={
                "estado": "JUSTIFICADO",
                "etiqueta": "LEGITIMO",
                "motivo": "Documentación consultada y verificada.",
                "revision_esperada": 0,
            },
        )
    db_session.rollback()
    db_session.refresh(r)
    assert r.estado_revision == "PENDIENTE"
    assert r.revision_numero == 0
    assert db_session.query(RevisionHistorica).count() == 0


@pytest.mark.parametrize(
    "url",
    [
        "/api/v1/analitica/modelos",
        "/api/v1/analitica/modelos/no-existe",
        "/api/v1/analitica/modelos/no-existe/evaluacion",
        "/api/v1/analitica/resultados?modelo_id=no-existe",
        "/api/v1/analitica/resultados/1",
    ],
)
def test_lecturas_exigen_autenticacion(client, url):
    assert client.get(url).status_code == 401


def test_trabajador_recuperado_no_publica_resultados(
    historico, usuario_admin, db_session, tmp_path, monkeypatch
):
    import joblib
    from sqlalchemy import update

    db = db_session
    j = trabajo(db, usuario_admin)
    guardar = joblib.dump

    def simular_recuperacion(*args, **kwargs):
        db.execute(
            update(ModeloHistorico)
            .where(ModeloHistorico.id == j.id)
            .values(estado="FALLIDO", plaza=None, error="Interrumpido")
        )
        db.commit()
        return guardar(*args, **kwargs)

    monkeypatch.setattr(joblib, "dump", simular_recuperacion)
    ejecutar(db, j.id, tmp_path)
    assert j.estado == "FALLIDO"
    assert db.query(ResultadoHistorico).count() == 0


def test_regla_conserva_su_orden_y_paginacion(
    client, historico, usuario_admin, db_session, tmp_path
):
    j = trabajo(db_session, usuario_admin)
    ejecutar(db_session, j.id, tmp_path)
    filas = db_session.query(ResultadoHistorico).order_by(ResultadoHistorico.score).limit(3).all()
    ids = [r.movimiento_id for r in filas]
    j.metricas = {**j.metricas, "top_regla": ids}
    db_session.commit()
    r = client.get(
        "/api/v1/analitica/resultados",
        headers=cabecera(usuario_admin),
        params={"modelo_id": j.id, "seleccion": "top_regla", "limite": 2, "pagina": 1},
    )
    assert [f["movimiento_id"] for f in r.json()["filas"]] == ids[:2]
    r = client.get(
        "/api/v1/analitica/resultados",
        headers=cabecera(usuario_admin),
        params={"modelo_id": j.id, "seleccion": "top_regla", "limite": 2, "pagina": 2},
    )
    assert [f["movimiento_id"] for f in r.json()["filas"]] == ids[2:]


def test_elegibilidad_congelada_al_encolar(
    historico, usuario_admin, db_session, tmp_path, monkeypatch
):
    from app.services import datos_analitica

    j = trabajo(db_session, usuario_admin)
    monkeypatch.setattr(datos_analitica, "seleccionar", lambda *args: ([], {}))
    ejecutar(db_session, j.id, tmp_path)
    assert j.estado == "COMPLETADO"
    assert db_session.query(ResultadoHistorico).count() == j.corte["perfil"]["elegibles"]


def test_error_despues_de_commit_no_reescribe_exito(
    historico, usuario_admin, db_session, tmp_path, monkeypatch
):
    j = trabajo(db_session, usuario_admin)
    commit = db_session.commit

    def commit_con_respuesta_perdida():
        terminado = j.estado == "COMPLETADO"
        commit()
        if terminado:
            raise OSError("Respuesta de commit perdida")

    monkeypatch.setattr(db_session, "commit", commit_con_respuesta_perdida)
    ejecutar(db_session, j.id, tmp_path)
    assert j.estado == "COMPLETADO"
    assert db_session.query(ResultadoHistorico).count() == 200
