"""Fallos de uso y recuperación comprobados fuera de la base institucional."""
import csv
import io

import pytest
from PIL import Image

from app.api.v1.endpoints import kardex, usuarios
from app.core.rate_limit import limiter
from app.core.security import create_access_token, verify_password
from app.models.auditoria import AuditoriaSistema
from app.models.kardex import SolicitudCargaKardex
from app.models.rol import Rol
from app.models.usuario import Usuario


def headers(usuario):
    return {"Authorization": "Bearer " + create_access_token(subject=usuario.id)}


@pytest.mark.parametrize("accion", ["crear", "editar", "desactivar", "reactivar", "password"])
def test_fallo_auditoria_revierte_cambio_de_usuario(
    client, db_session, usuario_admin, usuario_operador, monkeypatch, accion,
):
    if accion == "reactivar":
        usuario_operador.estado = "baja"
        db_session.commit()
    previo = (usuario_operador.nombre, usuario_operador.estado, usuario_operador.password_hash)
    cantidad = db_session.query(Usuario).count()
    uid = usuario_operador.id
    def fallar(*args, **kwargs):
        raise RuntimeError("Auditoría no disponible")
    monkeypatch.setattr(usuarios, "registrar_evento_auditoria", fallar)
    h = headers(usuario_admin)
    with pytest.raises(RuntimeError, match="Auditoría no disponible"):
        if accion == "crear":
            client.post("/api/v1/usuarios", headers=h, json={
                "nombre": "Cuenta QA", "email": "nueva@test.com", "password": "Password123!",
                "rol_id": usuario_operador.rol_id})
        elif accion == "editar":
            client.put(f"/api/v1/usuarios/{uid}", headers=h, json={"nombre": "Otro nombre"})
        elif accion == "password":
            client.post(f"/api/v1/usuarios/{uid}/resetear-password", headers=h,
                        json={"password_nuevo": "ClaveNueva123!"})
        else:
            client.patch(f"/api/v1/usuarios/{uid}/{accion}", headers=h)
    db_session.expire_all()
    actual = db_session.get(Usuario, uid)
    assert (actual.nombre, actual.estado, actual.password_hash) == previo
    assert db_session.query(Usuario).count() == cantidad
    assert db_session.query(AuditoriaSistema).count() == 0
    assert verify_password("Password123!", actual.password_hash)


@pytest.mark.parametrize("accion", ["crear", "editar", "reactivar"])
@pytest.mark.parametrize("invalido", ["inactivo", "sin_permisos"])
def test_no_habilita_cuentas_con_roles_no_utilizables(
    client, db_session, usuario_admin, usuario_operador, accion, invalido,
):
    rol = Rol(nombre="Operador" if invalido == "inactivo" else "Visitante",
              estado="baja" if invalido == "inactivo" else "activo")
    if invalido == "inactivo":
        rol = usuario_operador.rol
        rol.estado = "baja"
    else:
        db_session.add(rol)
    db_session.flush()
    if accion == "reactivar":
        usuario_operador.estado = "baja"
        usuario_operador.rol_id = rol.id
    db_session.commit()
    h = headers(usuario_admin)
    if accion == "crear":
        r = client.post("/api/v1/usuarios", headers=h, json={
            "nombre": "Cuenta QA", "email": "nueva@test.com", "password": "Password123!", "rol_id": rol.id})
    elif accion == "editar":
        r = client.put(f"/api/v1/usuarios/{usuario_operador.id}", headers=h, json={"rol_id": rol.id})
    else:
        r = client.patch(f"/api/v1/usuarios/{usuario_operador.id}/reactivar", headers=h)
    assert r.status_code == 409, r.text
    assert db_session.query(AuditoriaSistema).count() == 0


def test_correo_sin_distincion_de_mayusculas_y_sin_cuentas_duplicadas(
    client, db_session, usuario_admin, usuario_operador,
):
    limiter.reset()
    try:
        usuario_operador.email = "OperadorMixto@test.com"
        db_session.commit()
        r = client.post("/api/v1/auth/login", json={
            "email": "OPERADORMIXTO@TEST.COM", "password": "Password123!"})
        assert r.status_code == 200, r.text
        r = client.post("/api/v1/usuarios", headers=headers(usuario_admin), json={
            "nombre": "Duplicada", "email": "operadormixto@test.com", "password": "Password123!",
            "rol_id": usuario_operador.rol_id})
        assert r.status_code == 409, r.text
        r = client.put(f"/api/v1/usuarios/{usuario_operador.id}", headers=headers(usuario_admin),
                       json={"email": usuario_admin.email.upper()})
        assert r.status_code == 409, r.text
    finally:
        limiter.reset()


@pytest.mark.parametrize("campo,valor", [
    ("nombre", "   "),
    ("email", "a" * 60 + "@" + "b" * 60 + "." + "c" * 60 + ".com"),
])
def test_validacion_usuario_evitar_errores_de_columna(client, usuario_admin, campo, valor):
    payload = {"nombre": "Cuenta QA", "email": "nueva@test.com", "password": "Password123!",
               "rol_id": usuario_admin.rol_id, campo: valor}
    assert client.post("/api/v1/usuarios", headers=headers(usuario_admin), json=payload).status_code == 422
    assert client.put(f"/api/v1/usuarios/{usuario_admin.id}", headers=headers(usuario_admin),
                      json={campo: valor}).status_code == 422


def test_normaliza_nombre_sin_recortar_password(client, db_session, usuario_admin):
    password = " Clave con espacios! "
    r = client.post("/api/v1/usuarios", headers=headers(usuario_admin), json={
        "nombre": "  Cuenta QA  ", "email": "espacios@test.com", "password": password,
        "rol_id": usuario_admin.rol_id})
    assert r.status_code == 201, r.text
    assert r.json()["nombre"] == "Cuenta QA"
    assert verify_password(password, db_session.get(Usuario, r.json()["id"]).password_hash)


def test_reset_password_invalida_sesion_y_cookie_de_fotografias(client, usuario_admin, usuario_operador):
    limiter.reset()
    try:
        r = client.post("/api/v1/auth/login", json={
            "email": usuario_operador.email, "password": "Password123!"})
        assert r.status_code == 200
        vieja = {"Authorization": "Bearer " + r.json()["access_token"]}
        assert client.get("/api/v1/auth/me", headers=vieja).status_code == 200
        r = client.post(f"/api/v1/usuarios/{usuario_operador.id}/resetear-password",
            headers=headers(usuario_admin), json={"password_nuevo": "ClaveNuevaConSeguridad123!"})
        assert r.status_code == 200
        assert client.get("/api/v1/auth/me", headers=vieja).status_code == 401
        assert client.get("/storage/kardex_images/foto_privada.webp").status_code == 401
        nueva = client.post("/api/v1/auth/login", json={
            "email": usuario_operador.email, "password": "ClaveNuevaConSeguridad123!"})
        assert nueva.status_code == 200
        assert client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer " + nueva.json()["access_token"]}).status_code == 200
    finally:
        limiter.reset()


@pytest.mark.parametrize("huella", ["0" * 64, None, "ñ" * 64])
def test_huella_credencial_incorrecta_no_autoriza(client, usuario_admin, huella):
    token = create_access_token(subject=usuario_admin.id, extra_claims={"credencial": huella})
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + token}).status_code == 401


@pytest.mark.parametrize("reporte", ["inventario", "reglas"])
def test_csv_protege_formula_precedida_por_espacios_sin_cambiar_original(client, db_session, reporte):
    from test_reportes import _datos, _cabecera
    from app.models.kardex import MovimientoKardex
    usuario = _datos(db_session)
    m = db_session.query(MovimientoKardex).filter(MovimientoKardex.lote_id.isnot(None)).first()
    original = "  =HYPERLINK(\"https://example.invalid\")"
    m.detalle = original
    from app.models.activos import Activo
    articulo = db_session.get(Activo, m.articulo_id)
    articulo.nombre = original
    db_session.commit()
    ruta = "/api/v1/reportes/inventario.csv" if reporte == "inventario" else "/api/v1/analitica/reglas-historicas.csv"
    r = client.get(ruta, headers=_cabecera(usuario),
                   params={"gestion": m.fecha_movimiento.year, "seleccion": "todos"})
    assert r.status_code == 200
    filas = list(csv.reader(io.StringIO(r.text.lstrip("\ufeff")), delimiter=";"))
    assert any("'" + original in fila for fila in filas[1:])
    db_session.refresh(m)
    db_session.refresh(articulo)
    assert m.detalle == articulo.nombre == original


def test_fallo_ocr_no_expone_datos_privados_y_permite_reintentar(
    client, db_session, usuario_operador, tmp_path, monkeypatch,
):
    secreto = "api_key=secreto-no-publicable /carpeta/privada"
    def fallar(_):
        raise RuntimeError(secreto)
    monkeypatch.setattr(kardex, "procesar_lote_imagenes", fallar)
    monkeypatch.setattr(kardex, "STORAGE_DIR", str(tmp_path))
    previa = tmp_path / "evidencia_preexistente.webp"
    previa.write_bytes(b"evidencia anterior que debe conservarse")
    h = headers(usuario_operador)
    r = client.post("/api/v1/kardex/articulos", headers=h, json={"nombre": "Libro QA"})
    aid = r.json()["id"]
    foto = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(foto, format="PNG")
    r = client.post("/api/v1/kardex/upload-lote", headers=h, data={"articulo_id": aid},
                    files={"archivos": ("foto.png", foto.getvalue(), "image/png")})
    assert r.status_code == 503, r.text
    assert secreto not in r.text and "secreto-no-publicable" not in r.text
    assert "reintentar" in r.json()["detail"].lower()
    assert db_session.query(SolicitudCargaKardex).one().estado == "FALLIDO"
    assert list(tmp_path.iterdir()) == [previa]
    assert previa.read_bytes() == b"evidencia anterior que debe conservarse"


@pytest.mark.parametrize("misma_solicitud", [False, True])
def test_concurrencia_real_no_sobregira_ni_duplica_stock(
    client, db_session, usuario_admin, misma_solicitud,
):
    from concurrent.futures import ThreadPoolExecutor
    from datetime import UTC, datetime
    from threading import Barrier
    from uuid import uuid4
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from sqlalchemy.orm import sessionmaker
    from app.db.session import get_db
    from app.models.activos import Activo, CategoriaActivo, Existencia
    from app.models.area import Area
    from app.models.inventario import AperturaInventario
    from app.models.kardex import MovimientoKardex

    engine = db_session.get_bind()
    if engine.dialect.name != "postgresql":
        pytest.skip("La concurrencia requiere conexiones PostgreSQL independientes")
    assert (engine.url.database or "").startswith("activos_piloto_qa_")
    categoria = CategoriaActivo(nombre="Concurrencia QA")
    area = Area(nombre="Área concurrente QA", estado="activo")
    db_session.add_all([categoria, area])
    db_session.flush()
    articulo = Activo(categoria_id=categoria.id, codigo="CONC-QA", nombre="Libro QA")
    db_session.add(articulo)
    db_session.flush()
    apertura = AperturaInventario(articulo_id=articulo.id, cantidad_inicial=5,
        cantidad_actual=5, cantidad_sin_ubicacion=0, ultimo_moderno_id=0,
        aprobado_por=usuario_admin.id, aprobado_en=datetime.now(UTC),
        referencia_documento="ACTA-QA", justificacion="Prueba concurrente aislada")
    db_session.add_all([apertura, Existencia(activo_id=articulo.id, area_id=area.id,
                                            cantidad=5, estado="activo")])
    db_session.commit()
    h = headers(usuario_admin)
    aid, area_id = articulo.id, area.id
    cantidad = 2 if misma_solicitud else 4
    clave = str(uuid4())
    factory = sessionmaker(bind=engine)
    def conexion_independiente():
        with factory() as session:
            session.execute(text("SET LOCAL lock_timeout = '10s'"))
            session.execute(text("SET LOCAL statement_timeout = '20s'"))
            yield session
    previo = client.app.dependency_overrides[get_db]
    client.app.dependency_overrides[get_db] = conexion_independiente
    inicio = Barrier(2)
    def enviar(i):
        payload = {"solicitud_id": clave if misma_solicitud else str(uuid4()),
            "articulo_id": aid, "tipo": "salida", "cantidad": cantidad,
            "nodo_grafo": "Ventas", "tipo_operacion": "Ventas",
            "area_operativa_id": area_id, "receptor": "Cliente QA",
            "receptor_tipo": "PERSONA", "referencia_documento": "FACT-QA"}
        inicio.wait(timeout=10)
        return TestClient(client.app).post("/api/v1/kardex/movimiento-actual", headers=h, json=payload)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            respuestas = list(pool.map(enviar, range(2)))
    finally:
        client.app.dependency_overrides[get_db] = previo
    assert sorted(r.status_code for r in respuestas) == ([200, 200] if misma_solicitud else [200, 400]), [r.text for r in respuestas]
    if misma_solicitud:
        assert respuestas[0].json()["id"] == respuestas[1].json()["id"]
    db_session.expire_all()
    assert db_session.get(AperturaInventario, aid).cantidad_actual == 5 - cantidad
    assert db_session.query(Existencia).filter_by(activo_id=aid).one().cantidad == 5 - cantidad
    assert db_session.query(MovimientoKardex).filter_by(articulo_id=aid).count() == 1
    assert db_session.query(AuditoriaSistema).filter_by(accion="crear_movimiento_inventario").count() == 1
