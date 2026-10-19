from datetime import date
from io import BytesIO
from PIL import Image
from app.api.v1.endpoints import kardex
from app.models.kardex import LoteCarga, MovimientoKardex, SolicitudCargaKardex
from app.schemas.kardex import ExtraccionKardexHoja, FilaKardex
from app.services.datos_analitica import leer_corte, huella
from app.services.huella_lote import huella_de_paginas
from app.services.validacion_carga import preparar_imagen
from test_kardex import activos_prueba, auth_headers, crear_movimiento


def test_catalogo_oculta_ficha_descartada_vacia_y_conserva_historico(
    client, db_session, usuario_admin, activos_prueba,
):
    articulo, descartado = activos_prueba
    descartado.estado = "baja"
    db_session.commit()
    headers = auth_headers(usuario_admin)
    assert [a["id"] for a in client.get("/api/v1/kardex/articulos", headers=headers).json()] == [articulo.id]
    articulo.estado = "baja"
    db_session.commit()
    assert client.get("/api/v1/kardex/articulos", headers=headers).json() == []
    lote = LoteCarga(total_imagenes=1, tanda=3)
    db_session.add(lote)
    db_session.commit()
    movimiento = crear_movimiento(
        db_session, articulo_id=articulo.id, lote_id=lote.id,
        fecha=date(2025, 1, 1), saldo=5, ingresos=5, numero_pagina=1, orden_fila=1,
    )
    assert [a["id"] for a in client.get("/api/v1/kardex/articulos", headers=headers).json()] == [articulo.id]
    historial = client.get(f"/api/v1/kardex/historial/{articulo.id}", headers=headers).json()
    assert [m["id"] for m in historial] == [movimiento.id]


def test_tandas_filtran_historial_hil_y_no_cambian_corte(client, db_session, usuario_admin, activos_prueba):
    art, _ = activos_prueba
    ids = []
    for tanda in (1, 2, 3):
        lote = LoteCarga(total_imagenes=1, tanda=tanda)
        db_session.add(lote); db_session.commit()
        m = crear_movimiento(db_session, articulo_id=art.id, lote_id=lote.id,
            fecha=date(2025, 1, 1), saldo=10, ingresos=10, numero_pagina=1, orden_fila=1)
        m.tiene_error_saldo = True
        db_session.commit(); ids.append(m.id)
    moderno = crear_movimiento(db_session, articulo_id=art.id, fecha=date(2026, 1, 1), saldo=99, ingresos=99)
    antes = huella(leer_corte(db_session))
    headers = auth_headers(usuario_admin)
    for tanda, mid in zip((1, 2, 3), ids):
        historial = client.get(f"/api/v1/kardex/historial/{art.id}?tanda={tanda}", headers=headers).json()
        assert [m["id"] for m in historial] == [mid]
        assert historial[0]["tanda"] == tanda
        hil = client.get(f"/api/v1/kardex/errores?articulo_id={art.id}&tanda={tanda}", headers=headers).json()
        assert [m["id"] for m in hil] == [mid]
        assert hil[0]["tanda"] == tanda
    assert len(client.get(f"/api/v1/kardex/historial/{art.id}", headers=headers).json()) == 3
    assert client.get(f"/api/v1/kardex/historial/{art.id}?tanda=0", headers=headers).status_code == 422
    assert client.get('/api/v1/kardex/errores?tanda=10000', headers=headers).status_code == 422
    modern = client.get(f"/api/v1/kardex/historial-actual/{art.id}", headers=headers).json()
    assert modern[0]["id"] == moderno.id and modern[0]["tanda"] is None
    resumen = client.get('/api/v1/kardex/tandas', headers=headers).json()
    assert resumen["tanda_nuevas_cargas"] == 3
    assert [t["movimientos"] for t in resumen["tandas"]] == [1, 1, 1]
    assert huella(leer_corte(db_session)) == antes
    # La procedencia no participa en el corte, aun si se cambia la etiqueta en una copia.
    db_session.get(LoteCarga, db_session.get(MovimientoKardex, ids[0]).lote_id).tanda = 2
    db_session.commit()
    assert huella(leer_corte(db_session)) == antes


def preparar_ocr(monkeypatch, tmp_path, titulo):
    monkeypatch.setattr(kardex, "STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(kardex, "procesar_lote_imagenes", lambda _: [ExtraccionKardexHoja(
        nombre_articulo=titulo, filas=[FilaKardex(fecha=date(2025, 1, 1), detalle="Inicial", ingresos=5, saldo_registrado=5, orden_fila=1)])])
    b = BytesIO(); Image.new("RGB", (8, 8)).save(b, "PNG")
    return b.getvalue()


def cargar(client, usuario, art, imagen):
    return client.post('/api/v1/kardex/upload-lote', headers=auth_headers(usuario),
        data={"articulo_id": art.id}, files=[("archivos", ("hoja.png", imagen, "image/png"))])


def test_nuevos_escaneos_son_tanda_3_y_duplicado_conserva_tanda(client, db_session, usuario_operador, activos_prueba, monkeypatch, tmp_path):
    art, _ = activos_prueba
    imagen = preparar_ocr(monkeypatch, tmp_path, art.nombre)
    r = cargar(client, usuario_operador, art, imagen)
    assert r.status_code == 200 and r.json()["tanda"] == 3
    lote = db_session.get(LoteCarga, r.json()["lote_id"])
    solicitud = db_session.query(SolicitudCargaKardex).one()
    assert lote.tanda == solicitud.tanda == 3
    # Simular la procedencia anterior sin recrear el movimiento ni su evidencia.
    lote.tanda = solicitud.tanda = 1; db_session.commit()
    r = cargar(client, usuario_operador, art, imagen)
    assert r.status_code == 200 and r.json()["duplicado"] is True and r.json()["tanda"] == 1
    assert db_session.query(LoteCarga).count() == 1
    assert db_session.query(MovimientoKardex).count() == 1


def test_confirmacion_y_reintento_conservan_tanda_de_solicitud(client, db_session, usuario_operador, activos_prueba, monkeypatch, tmp_path):
    art, _ = activos_prueba
    imagen = preparar_ocr(monkeypatch, tmp_path, "ARTICULO TOTALMENTE DISTINTO")
    r = cargar(client, usuario_operador, art, imagen)
    assert r.status_code == 200 and r.json()["requiere_confirmacion"] is True
    assert r.json()["tanda"] == 3
    r2 = cargar(client, usuario_operador, art, imagen)
    assert r2.json()["tanda"] == 3 and r2.json()["pendiente_id"] == r.json()["pendiente_id"]
    solicitud = db_session.query(SolicitudCargaKardex).one()
    solicitud.tanda = 1; db_session.commit()
    path = f'/api/v1/kardex/lotes-pendientes/{r.json()["pendiente_id"]}/decision'
    r = client.post(path, headers=auth_headers(usuario_operador), json={"confirmar":True})
    assert r.status_code == 200 and r.json()["tanda"] == 1
    assert db_session.get(LoteCarga, r.json()["lote_id"]).tanda == 1
    assert client.post(path, headers=auth_headers(usuario_operador), json={"confirmar":True}).json()["tanda"] == 1


def test_resumen_sin_token_denegado(client):
    assert client.get('/api/v1/kardex/tandas').status_code == 401


def test_se_puede_completar_tanda_anterior_explicita_sin_cambiar_tanda_actual(
    client, db_session, usuario_operador, activos_prueba, monkeypatch, tmp_path,
):
    art, _ = activos_prueba
    imagen = preparar_ocr(monkeypatch, tmp_path, art.nombre)
    respuesta = client.post('/api/v1/kardex/upload-lote', headers=auth_headers(usuario_operador),
        data={"articulo_id": art.id, "tanda": 2}, files=[("archivos", ("hoja.png", imagen, "image/png"))])
    assert respuesta.status_code == 200 and respuesta.json()["tanda"] == 2
    assert db_session.get(LoteCarga, respuesta.json()["lote_id"]).tanda == 2
    assert client.get('/api/v1/kardex/tandas',headers=auth_headers(usuario_operador)).json()["tanda_nuevas_cargas"] == 3


def test_reintento_tras_reinicio_conserva_una_sola_carga(
    client, db_session, usuario_operador, activos_prueba, monkeypatch, tmp_path,
):
    art, _ = activos_prueba
    imagen = preparar_ocr(monkeypatch, tmp_path, art.nombre)
    huella = huella_de_paginas([preparar_imagen(imagen, "image/png")])
    solicitud = SolicitudCargaKardex(
        articulo_id=art.id, huella=huella, estado="PROCESANDO", tanda=2,
        usuario_id=usuario_operador.id, intento=1,
        servidor_instancia="instancia-antes-del-reinicio",
    )
    db_session.add(solicitud)
    db_session.commit()
    ruta = f"/api/v1/kardex/solicitudes?articulo_id={art.id}"
    estado = client.get(ruta, headers=auth_headers(usuario_operador)).json()
    assert estado[0]["reintentable"] is True
    respuesta = cargar(client, usuario_operador, art, imagen)
    assert respuesta.status_code == 200
    assert db_session.query(LoteCarga).count() == 1
    assert db_session.query(MovimientoKardex).count() == 1
    db_session.refresh(solicitud)
    assert solicitud.estado == "COMPLETADO" and solicitud.intento == 2
    assert client.get(ruta, headers=auth_headers(usuario_operador)).json()[0]["reintentable"] is False
    assert cargar(client, usuario_operador, art, imagen).json()["duplicado"] is True
    assert db_session.query(LoteCarga).count() == 1
