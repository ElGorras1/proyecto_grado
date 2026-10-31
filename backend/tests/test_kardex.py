from datetime import date
from io import BytesIO
from PIL import Image
from app.models.kardex import LotePendiente
from app.schemas.kardex import ExtraccionKardexHoja, FilaKardex
from app.api.v1.endpoints import kardex

import pytest

from app.core.security import create_access_token, hash_password
from app.models.activos import Activo, CategoriaActivo
from app.models.auditoria import AuditoriaSistema
from app.models.kardex import LoteCarga, MovimientoKardex
from app.models.kardex import SolicitudCargaKardex
from app.services.huella_lote import huella_de_paginas
from app.services.kardex_service import calcular_y_validar_saldos
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.services.clasificador_nodos import (
    NODO_DESTINO_NO_ESPECIFICADO,
    NODO_ORIGEN_NO_ESPECIFICADO,
)


def auth_headers(usuario: Usuario) -> dict[str, str]:
    token = create_access_token(
        subject=usuario.id,
        extra_claims={"rol": usuario.rol.nombre},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("confirmar", [True, False])
def test_confirmacion_titulos_conserva_extraccion_y_no_duplica(
    client, db_session, usuario_operador, usuario_admin, activos_prueba,
    monkeypatch, tmp_path, confirmar,
):
    articulo, _ = activos_prueba
    llamadas = []
    def extraer(paths):
        llamadas.append(paths)
        return [ExtraccionKardexHoja(
            nombre_articulo="MUSICA CONTEMPORANEA LIBRO PARTITURAS",
            filas=[FilaKardex(fecha=date(2020, 1, 1), detalle="Inicial",
                             ingresos=5, saldo_registrado=5, orden_fila=1)],
        )]
    monkeypatch.setattr(kardex, "procesar_lote_imagenes", extraer)
    monkeypatch.setattr(kardex, "STORAGE_DIR", str(tmp_path))
    imagen = BytesIO()
    Image.new("RGB", (8, 8)).save(imagen, "PNG")
    respuesta = client.post(
        "/api/v1/kardex/upload-lote", headers=auth_headers(usuario_operador),
        data={"articulo_id": articulo.id},
        files=[("archivos", ("pagina.png", imagen.getvalue(), "image/png"))],
    )
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["requiere_confirmacion"] is True
    assert datos["diferencias"][0]["pagina"] == 1
    repeticion = client.post(
        "/api/v1/kardex/upload-lote", headers=auth_headers(usuario_operador),
        data={"articulo_id": articulo.id},
        files=[("archivos", ("pagina.png", imagen.getvalue(), "image/png"))],
    )
    assert repeticion.status_code == 200
    assert repeticion.json()["pendiente_id"] == datos["pendiente_id"]
    assert db_session.query(MovimientoKardex).count() == 0
    assert db_session.query(LoteCarga).count() == 0
    ruta = f'/api/v1/kardex/lotes-pendientes/{datos["pendiente_id"]}/decision'
    assert client.post(ruta, json={"confirmar": confirmar}).status_code == 401
    assert client.post(ruta, headers=auth_headers(usuario_admin),
                       json={"confirmar": confirmar}).status_code == 404
    for _ in range(2):
        resultado = client.post(ruta, headers=auth_headers(usuario_operador),
                                json={"confirmar": confirmar})
        assert resultado.status_code == 200
    assert len(llamadas) == 1
    assert db_session.query(MovimientoKardex).count() == int(confirmar)
    assert db_session.query(LoteCarga).count() == int(confirmar)
    pendiente = db_session.query(LotePendiente).one()
    assert pendiente.estado == ("CONFIRMADO" if confirmar else "CANCELADO")
    accion = "confirmar_titulos_lote" if confirmar else "cancelar_titulos_lote"
    evento = db_session.query(AuditoriaSistema).filter_by(accion=accion).one()
    assert evento.usuario_id == usuario_operador.id
    assert evento.detalle["diferencias"] == datos["diferencias"]


def test_reintentar_mismas_fotos_no_duplica_movimientos_ni_ocr(
    client, db_session, usuario_operador, activos_prueba, monkeypatch, tmp_path,
):
    articulo, _ = activos_prueba
    llamadas = []

    def extraer(paths):
        llamadas.append(paths)
        return [ExtraccionKardexHoja(
            nombre_articulo=articulo.nombre,
            filas=[FilaKardex(fecha=date(2020, 1, 1), detalle="Inicial",
                             ingresos=5, saldo_registrado=5, orden_fila=1)],
        )]

    monkeypatch.setattr(kardex, "procesar_lote_imagenes", extraer)
    monkeypatch.setattr(kardex, "STORAGE_DIR", str(tmp_path))
    imagen = BytesIO()
    Image.new("RGB", (8, 8), color="red").save(imagen, "PNG")

    def subir():
        return client.post(
            "/api/v1/kardex/upload-lote", headers=auth_headers(usuario_operador),
            data={"articulo_id": articulo.id},
            files=[("archivos", ("pagina.png", imagen.getvalue(), "image/png"))],
        )

    primera = subir()
    segunda = subir()
    assert primera.status_code == 200
    assert segunda.status_code == 200
    assert segunda.json()["duplicado"] is True
    assert segunda.json()["lote_id"] == primera.json()["lote_id"]
    assert len(llamadas) == 1
    assert db_session.query(LoteCarga).count() == 1
    assert db_session.query(MovimientoKardex).count() == 1
    assert db_session.query(SolicitudCargaKardex).count() == 1


def test_reintento_tras_error_ocr_reutiliza_huella_sin_duplicar(
    client, db_session, usuario_operador, activos_prueba, monkeypatch, tmp_path,
):
    articulo, _ = activos_prueba
    intentos = []

    def extraer(paths):
        intentos.append(paths)
        if len(intentos) == 1:
            raise RuntimeError("OCR temporalmente indisponible")
        return [ExtraccionKardexHoja(
            nombre_articulo=articulo.nombre,
            filas=[FilaKardex(fecha=date(2020, 1, 1), detalle="Inicial",
                             ingresos=3, saldo_registrado=3, orden_fila=1)],
        )]

    monkeypatch.setattr(kardex, "procesar_lote_imagenes", extraer)
    monkeypatch.setattr(kardex, "STORAGE_DIR", str(tmp_path))
    imagen = BytesIO()
    Image.new("RGB", (8, 8), color="blue").save(imagen, "PNG")

    def subir():
        return client.post(
            "/api/v1/kardex/upload-lote", headers=auth_headers(usuario_operador),
            data={"articulo_id": articulo.id},
            files=[("archivos", ("pagina.png", imagen.getvalue(), "image/png"))],
        )

    assert subir().status_code == 503
    assert db_session.query(SolicitudCargaKardex).one().estado == "FALLIDO"
    assert subir().status_code == 200
    assert len(intentos) == 2
    assert db_session.query(SolicitudCargaKardex).one().estado == "COMPLETADO"
    assert db_session.query(MovimientoKardex).count() == 1


def test_carga_igual_en_proceso_responde_conflicto_sin_crear_otro_lote(
    client, db_session, usuario_operador, activos_prueba, monkeypatch, tmp_path,
):
    articulo, _ = activos_prueba
    monkeypatch.setattr(kardex, "STORAGE_DIR", str(tmp_path))
    imagen = BytesIO()
    Image.new("RGB", (8, 8), color="green").save(imagen, "PNG")
    salida = BytesIO()
    Image.open(BytesIO(imagen.getvalue())).save(salida, "webp", quality=60)
    db_session.add(SolicitudCargaKardex(
        articulo_id=articulo.id, huella=huella_de_paginas([salida.getvalue()]),
        estado="PROCESANDO", usuario_id=usuario_operador.id,
    ))
    db_session.commit()

    respuesta = client.post(
        "/api/v1/kardex/upload-lote", headers=auth_headers(usuario_operador),
        data={"articulo_id": articulo.id},
        files=[("archivos", ("pagina.png", imagen.getvalue(), "image/png"))],
    )
    assert respuesta.status_code == 409
    assert db_session.query(LoteCarga).count() == 0
    assert db_session.query(MovimientoKardex).count() == 0
    assert not list(tmp_path.iterdir())


@pytest.fixture
def usuario_auditor(db_session):
    rol = Rol(nombre="Auditor", descripcion="Rol auditor", estado="activo")
    db_session.add(rol)
    db_session.commit()

    usuario = Usuario(
        rol_id=rol.id,
        nombre="Auditor de Kárdex",
        email="auditor_kardex@test.com",
        password_hash=hash_password("Password123!"),
        estado="activo",
    )
    db_session.add(usuario)
    db_session.commit()
    return usuario


@pytest.fixture
def activos_prueba(db_session):
    categoria = CategoriaActivo(
        nombre="Categoría Kárdex",
        codigo="CAT-KDX",
        estado="activo",
    )
    db_session.add(categoria)
    db_session.flush()

    principal = Activo(
        categoria_id=categoria.id,
        codigo="KDX-PRINCIPAL",
        nombre="Artículo principal",
        unidad_medida="unidad",
        estado="activo",
    )
    secundario = Activo(
        categoria_id=categoria.id,
        codigo="KDX-SECUNDARIO",
        nombre="Artículo secundario",
        unidad_medida="unidad",
        estado="activo",
    )
    db_session.add_all([principal, secundario])
    db_session.commit()
    return principal, secundario


def crear_movimiento(
    db_session,
    *,
    articulo_id: int,
    fecha: date,
    saldo: int,
    ingresos: int | None = None,
    salidas: int | None = None,
    lote_id: int | None = None,
    numero_pagina: int | None = None,
    orden_fila: int | None = None,
    detalle: str = "Movimiento de prueba",
) -> MovimientoKardex:
    movimiento = MovimientoKardex(
        articulo_id=articulo_id,
        lote_id=lote_id,
        fecha_movimiento=fecha,
        detalle=detalle,
        ingresos=ingresos,
        salidas=salidas,
        saldo_registrado=saldo,
        saldo_calculado=saldo,
        numero_pagina=numero_pagina,
        orden_fila=orden_fila,
        tiene_error_saldo=False,
        requiere_auditoria_nodo=False,
        estado="ACTIVO",
    )
    db_session.add(movimiento)
    db_session.commit()
    db_session.refresh(movimiento)
    return movimiento


def test_movimiento_actual_rechaza_salida_con_stock_insuficiente(
    client,
    db_session,
    usuario_operador,
    usuario_admin,
    activos_prueba,
):
    articulo, _ = activos_prueba
    crear_movimiento(
        db_session,
        articulo_id=articulo.id,
        fecha=date(2026, 9, 1),
        saldo=5,
        ingresos=5,
    )
    cantidad_inicial = db_session.query(MovimientoKardex).count()

    apertura = client.post(f"/api/v1/kardex/articulos/{articulo.id}/apertura",
        headers=auth_headers(usuario_admin), json={"cantidad": 5,
        "referencia_documento": "ACTA-TEST", "justificacion": "Conteo físico de prueba", "conteo_verificado": True})
    assert apertura.status_code == 200

    response = client.post(
        "/api/v1/kardex/movimiento-actual",
        headers=auth_headers(usuario_operador),
        json={
            "articulo_id": articulo.id,
            "solicitud_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "tipo": "salida",
            "cantidad": 6,
            "nodo_grafo": "Ventas",
            "tipo_operacion": "Ventas",
            "receptor": "Cliente de prueba",
            "receptor_tipo": "PERSONA",
            "referencia_documento": "FACT-TEST",
        },
    )

    assert response.status_code == 400
    assert "Stock insuficiente" in response.json()["detail"]
    assert db_session.query(MovimientoKardex).count() == cantidad_inicial
    assert (
        db_session.query(AuditoriaSistema)
        .filter(AuditoriaSistema.accion == "crear_movimiento_inventario")
        .count()
        == 0
    )


def test_movimiento_actual_persiste_saldo_operador_y_auditoria(
    client,
    db_session,
    usuario_operador,
    usuario_admin,
    activos_prueba,
):
    articulo, _ = activos_prueba

    apertura = client.post(f"/api/v1/kardex/articulos/{articulo.id}/apertura",
        headers=auth_headers(usuario_admin), json={"cantidad": 0,
        "referencia_documento": "ACTA-TEST", "justificacion": "Conteo físico de prueba", "conteo_verificado": True})
    assert apertura.status_code == 200

    response = client.post(
        "/api/v1/kardex/movimiento-actual",
        headers=auth_headers(usuario_operador),
        json={
            "articulo_id": articulo.id,
            "solicitud_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            "tipo": "ingreso",
            "cantidad": 8,
            "nodo_grafo": "Inventario / Compra",
            "tipo_operacion": "Inventario / Compra",
            "observaciones": "Saldo inicial de prueba",
            "referencia_documento": "ACTA-COMPRA",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ingresos"] == 8
    assert data["salidas"] is None
    assert data["saldo_registrado"] == 8
    assert data["usuario_operador"] == usuario_operador.nombre
    assert data["encargado_id"] == usuario_operador.id
    assert data["usuario_registrador_id"] == usuario_operador.id
    assert data["encargado_nombre"] == usuario_operador.nombre

    evento = (
        db_session.query(AuditoriaSistema)
        .filter(
            AuditoriaSistema.accion == "crear_movimiento_inventario",
            AuditoriaSistema.recurso_id == data["id"],
        )
        .one()
    )
    assert evento.usuario_id == usuario_operador.id
    assert evento.detalle["nuevo_saldo"] == 8


def test_encargado_distinto_del_registrador_y_cuenta_inactiva_rechazada(
    client, db_session, usuario_admin, usuario_operador, activos_prueba,
):
    articulo, _ = activos_prueba
    apertura = client.post(
        f"/api/v1/kardex/articulos/{articulo.id}/apertura",
        headers=auth_headers(usuario_admin),
        json={"cantidad": 5, "referencia_documento": "ACTA-TEST",
              "justificacion": "Conteo físico", "conteo_verificado": True},
    )
    assert apertura.status_code == 200
    opciones = client.get("/api/v1/kardex/encargados",
                          headers=auth_headers(usuario_operador))
    assert opciones.status_code == 200
    assert {u["id"] for u in opciones.json()} == {usuario_admin.id, usuario_operador.id}

    payload = {"articulo_id": articulo.id, "encargado_id": usuario_admin.id,
               "solicitud_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
               "tipo": "salida", "cantidad": 2, "nodo_grafo": "Ventas",
               "referencia_documento": "ACTA-TEST"}
    respuesta = client.post("/api/v1/kardex/movimiento-actual",
                             headers=auth_headers(usuario_operador), json=payload)
    assert respuesta.status_code == 200
    movimiento = respuesta.json()
    assert (movimiento["encargado_id"], movimiento["usuario_registrador_id"]) == (
        usuario_admin.id, usuario_operador.id)
    assert movimiento["encargado_nombre"] == usuario_admin.nombre
    assert movimiento["usuario_operador"] == usuario_operador.nombre
    evento = db_session.query(AuditoriaSistema).filter_by(
        accion="crear_movimiento_inventario", recurso_id=movimiento["id"]).one()
    assert evento.detalle["encargado_id"] == usuario_admin.id
    assert evento.detalle["usuario_registrador_id"] == usuario_operador.id

    usuario_admin.estado = "inactivo"
    db_session.commit()
    assert usuario_admin.id not in {u["id"] for u in client.get(
        "/api/v1/kardex/encargados", headers=auth_headers(usuario_operador)).json()}
    rechazada = client.post("/api/v1/kardex/movimiento-actual",
                            headers=auth_headers(usuario_operador),
                            json={**payload, "solicitud_id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd"})
    assert rechazada.status_code == 422
    assert db_session.query(MovimientoKardex).filter_by(articulo_id=articulo.id).count() == 1


def test_movimiento_actual_rechaza_nodo_vacio(
    client,
    usuario_operador,
    activos_prueba,
):
    articulo, _ = activos_prueba

    response = client.post(
        "/api/v1/kardex/movimiento-actual",
        headers=auth_headers(usuario_operador),
        json={
            "articulo_id": articulo.id,
            "solicitud_id": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
            "tipo": "ingreso",
            "cantidad": 1,
            "nodo_grafo": "   ",
            "referencia_documento": "ACTA-TEST",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Debe seleccionar un nodo para la operación."


def test_endpoints_kardex_protegidos_devuelven_401_sin_token(client):
    requests = [
        (
            "POST",
            "/api/v1/kardex/upload-lote",
            {
                "data": {"articulo_id": "1"},
                "files": [("archivos", ("pagina.png", b"imagen", "image/png"))],
            },
        ),
        (
            "PUT",
            "/api/v1/kardex/movimiento/1",
            {"json": {"saldo_registrado": 0}},
        ),
        ("POST", "/api/v1/kardex/articulos", {"json": {"nombre": "Artículo"}}),
        ("GET", "/api/v1/kardex/articulos", {}),
        ("GET", "/api/v1/kardex/errores", {}),
        ("GET", "/api/v1/kardex/grafo/1", {}),
        ("GET", "/api/v1/kardex/nodos", {}),
        ("GET", "/api/v1/kardex/ferias", {}),
        ("GET", "/api/v1/kardex/catalogo-areas", {}),
        ("GET", "/api/v1/kardex/historial/1", {}),
        ("GET", "/api/v1/kardex/historial-actual/1", {}),
        (
            "POST",
            "/api/v1/kardex/movimiento-actual",
            {
                "json": {
                    "articulo_id": 1,
                    "tipo": "ingreso",
                    "cantidad": 1,
                    "nodo_grafo": "Inventario / Compra",
                }
            },
        ),
        ("POST", "/api/v1/kardex/movimiento-actual/1/anular", {}),
    ]

    for method, path, kwargs in requests:
        response = client.request(method, path, **kwargs)
        assert response.status_code == 401, f"{method} {path} devolvió {response.status_code}"


def test_auditor_puede_consultar_pero_no_mutar_kardex(
    client,
    usuario_auditor,
):
    headers = auth_headers(usuario_auditor)

    assert client.get("/api/v1/kardex/articulos", headers=headers).status_code == 200

    mutations = [
        (
            "POST",
            "/api/v1/kardex/upload-lote",
            {
                "data": {"articulo_id": "1"},
                "files": [("archivos", ("pagina.png", b"imagen", "image/png"))],
            },
        ),
        (
            "PUT",
            "/api/v1/kardex/movimiento/1",
            {"json": {"saldo_registrado": 0}},
        ),
        ("POST", "/api/v1/kardex/articulos", {"json": {"nombre": "Artículo"}}),
        (
            "POST",
            "/api/v1/kardex/movimiento-actual",
            {
                "json": {
                    "articulo_id": 1,
                    "tipo": "ingreso",
                    "cantidad": 1,
                    "nodo_grafo": "Inventario / Compra",
                }
            },
        ),
        ("POST", "/api/v1/kardex/movimiento-actual/1/anular", {}),
    ]

    for method, path, kwargs in mutations:
        response = client.request(method, path, headers=headers, **kwargs)
        assert response.status_code == 403, f"{method} {path} devolvió {response.status_code}"


def test_historial_legacy_filtra_por_lote_articulo_y_orden(
    client,
    db_session,
    usuario_admin,
    activos_prueba,
):
    articulo, otro_articulo = activos_prueba
    lote = LoteCarga(total_imagenes=2)
    db_session.add(lote)
    db_session.commit()

    legacy_posterior = crear_movimiento(
        db_session,
        articulo_id=articulo.id,
        lote_id=lote.id,
        fecha=date(2019, 2, 1),
        saldo=8,
        salidas=2,
        numero_pagina=2,
        orden_fila=1,
        detalle="Legacy posterior",
    )
    legacy_anterior = crear_movimiento(
        db_session,
        articulo_id=articulo.id,
        lote_id=lote.id,
        fecha=date(2019, 1, 1),
        saldo=10,
        ingresos=10,
        numero_pagina=1,
        orden_fila=1,
        detalle="Legacy anterior",
    )
    lote_siguiente = LoteCarga(total_imagenes=1)
    db_session.add(lote_siguiente)
    db_session.commit()
    legacy_tercero = crear_movimiento(
        db_session,
        articulo_id=articulo.id,
        lote_id=lote_siguiente.id,
        fecha=date(2018, 12, 1),  # La fecha física puede estar mal escrita.
        saldo=7,
        salidas=1,
        numero_pagina=1,
        orden_fila=1,
        detalle="Tercera hoja en otra carga",
    )
    crear_movimiento(
        db_session,
        articulo_id=articulo.id,
        fecha=date(2026, 1, 1),
        saldo=12,
        ingresos=2,
        detalle="Movimiento moderno",
    )
    crear_movimiento(
        db_session,
        articulo_id=otro_articulo.id,
        lote_id=lote.id,
        fecha=date(2018, 1, 1),
        saldo=99,
        ingresos=99,
        numero_pagina=1,
        orden_fila=1,
        detalle="Legacy de otro artículo",
    )

    response = client.get(
        f"/api/v1/kardex/historial/{articulo.id}",
        headers=auth_headers(usuario_admin),
    )

    assert response.status_code == 200
    ids = [movimiento["id"] for movimiento in response.json()]
    assert ids == [legacy_anterior.id, legacy_posterior.id, legacy_tercero.id]
    assert [m["lote_id"] for m in response.json()] == [lote.id, lote.id, lote_siguiente.id]


def test_nueva_hoja_individual_toma_saldo_del_ultimo_lote_no_de_la_fila_mas_alta(
    db_session, activos_prueba,
):
    articulo, _ = activos_prueba
    lote_primero = LoteCarga(total_imagenes=1)
    lote_segundo = LoteCarga(total_imagenes=1)
    db_session.add_all([lote_primero, lote_segundo])
    db_session.commit()
    crear_movimiento(db_session, articulo_id=articulo.id, lote_id=lote_primero.id,
                     fecha=date(2020, 1, 1), saldo=10, ingresos=10,
                     numero_pagina=1, orden_fila=1)
    crear_movimiento(db_session, articulo_id=articulo.id, lote_id=lote_primero.id,
                     fecha=date(2020, 1, 2), saldo=20, ingresos=10,
                     numero_pagina=1, orden_fila=2)
    crear_movimiento(db_session, articulo_id=articulo.id, lote_id=lote_segundo.id,
                     fecha=date(2020, 1, 3), saldo=17, salidas=3,
                     numero_pagina=1, orden_fila=1)
    pagina = ExtraccionKardexHoja(
        nombre_articulo=articulo.nombre,
        filas=[FilaKardex(fecha=date(2020, 1, 4), detalle="Salida siguiente",
                          salidas=2, saldo_registrado=15, orden_fila=1)],
    )
    resultado = calcular_y_validar_saldos(
        db_session, articulo.id, [pagina], lote_segundo.id + 1, ["foto.webp"],
    )
    assert resultado[0].saldo_calculado == 15
    assert resultado[0].tiene_error_saldo is False


def test_historial_moderno_excluye_movimientos_legacy(
    client,
    db_session,
    usuario_admin,
    activos_prueba,
):
    articulo, _ = activos_prueba
    lote = LoteCarga(total_imagenes=1)
    db_session.add(lote)
    db_session.commit()

    crear_movimiento(
        db_session,
        articulo_id=articulo.id,
        lote_id=lote.id,
        fecha=date(2020, 1, 1),
        saldo=5,
        ingresos=5,
    )
    moderno = crear_movimiento(
        db_session,
        articulo_id=articulo.id,
        fecha=date(2026, 9, 1),
        saldo=7,
        ingresos=2,
    )

    response = client.get(
        f"/api/v1/kardex/historial-actual/{articulo.id}",
        headers=auth_headers(usuario_admin),
    )

    assert response.status_code == 200
    assert [movimiento["id"] for movimiento in response.json()] == [moderno.id]
    assert response.json()[0]["lote_id"] is None


def test_grafo_separa_origen_y_destino_no_especificados(
    client,
    db_session,
    usuario_admin,
    activos_prueba,
):
    articulo, _ = activos_prueba
    primero = crear_movimiento(
        db_session,
        articulo_id=articulo.id,
        fecha=date(2020, 1, 1),
        saldo=3,
        ingresos=3,
    )
    segundo = crear_movimiento(
        db_session,
        articulo_id=articulo.id,
        fecha=date(2020, 1, 2),
        saldo=1,
        salidas=2,
    )
    primero.nodo_grafo = None
    segundo.nodo_grafo = "Desconocido / Sin Asignar"
    db_session.commit()

    response = client.get(
        f"/api/v1/kardex/grafo/{articulo.id}",
        headers=auth_headers(usuario_admin),
    )

    assert response.status_code == 200
    data = response.json()
    origen = next(item for item in data["nodes"] if item["name"] == NODO_ORIGEN_NO_ESPECIFICADO)
    destino = next(item for item in data["nodes"] if item["name"] == NODO_DESTINO_NO_ESPECIFICADO)
    assert origen["tipo"] == "sin_area_registrada"
    assert destino["tipo"] == "sin_area_registrada"
    assert origen["requiere_auditoria"] is False
    assert destino["requiere_auditoria"] is False
    assert {
        "source": NODO_ORIGEN_NO_ESPECIFICADO,
        "target": "Almacén Central",
        "value": 3,
    } in data["links"]
    assert {
        "source": "Almacén Central",
        "target": NODO_DESTINO_NO_ESPECIFICADO,
        "value": 2,
    } in data["links"]


def test_grafo_conserva_ida_y_vuelta_y_marca_area_con_revision_pendiente(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, _ = activos_prueba
    for ingreso, salida in [(10, None), (None, 4)]:
        mov = crear_movimiento(db_session, articulo_id=articulo.id,
                              fecha=date(2020, 1, 1), saldo=10,
                              ingresos=ingreso, salidas=salida)
        mov.nodo_grafo = "Área: CEDOAL"
        mov.area_estado = "PENDIENTE_HIL"
    db_session.commit()
    response = client.get(f"/api/v1/kardex/grafo/{articulo.id}", headers=auth_headers(usuario_admin))
    assert response.status_code == 200
    data = response.json()
    assert next(n for n in data["nodes"] if n["name"] == "Área: CEDOAL")["requiere_auditoria"] is True
    assert {"source": "Área: CEDOAL", "target": "Almacén Central", "value": 10} in data["links"]
    assert {"source": "Almacén Central", "target": "Área: CEDOAL", "value": 4} in data["links"]
