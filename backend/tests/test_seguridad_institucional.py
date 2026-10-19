from datetime import UTC, datetime, timedelta

import pytest
import jwt
from test_analitica import cabecera

from app.api import evidencia
from app.core.config import settings
from app.core.security import create_access_token


def test_fotos_exigen_sesion_y_no_exponen_rutas(client, usuario_admin, tmp_path, monkeypatch):
    monkeypatch.setattr(evidencia, "RAIZ", tmp_path)
    (tmp_path / "pagina.webp").write_bytes(b"contenido-de-prueba")
    (tmp_path / "secreto.env").write_text("dato-privado")
    assert client.get("/storage/pagina.webp").status_code == 401
    h = cabecera(usuario_admin)
    r = client.get("/storage/pagina.webp", headers=h)
    assert r.status_code == 200 and r.content == b"contenido-de-prueba"
    assert r.headers["content-type"] == "image/webp"
    assert r.headers["cache-control"] == "private, no-store"
    assert client.get("/storage/secreto.env", headers=h).status_code == 404
    assert client.get("/storage/%2e%2e/secreto.env", headers=h).status_code == 404
    assert client.get("/storage/%00.webp", headers=h).status_code == 404
    me = client.get("/api/v1/auth/me", headers=h)
    assert "HttpOnly" in me.headers["set-cookie"] and "Path=/storage" in me.headers["set-cookie"]
    assert client.get("/storage/pagina.webp").status_code == 200
    # La cookie de imágenes no autoriza negocios.
    assert client.get("/api/v1/analitica-operativa/perfil").status_code == 401
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/storage/pagina.webp").status_code == 401


def test_tokens_invalidos_baja_y_rol_desactivado_revocan_acceso(client, usuario_admin, db_session):
    for sub in ("no-numero", "", "1e100"):
        h = {"Authorization": "Bearer " + create_access_token(sub)}
        assert client.get("/api/v1/auth/me", headers=h).status_code == 401
    expirado = jwt.encode(
        {"sub": str(usuario_admin.id), "exp": datetime.now(UTC) - timedelta(seconds=1)},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + expirado}).status_code
        == 401
    )
    h = cabecera(usuario_admin)
    usuario_admin.rol.estado = "baja"
    db_session.commit()
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401
    usuario_admin.rol.estado = "activo"
    usuario_admin.estado = "baja"
    db_session.commit()
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401


def test_rol_desconocido_no_hereda_lectura_y_claim_no_eleva_privilegios(
    client, usuario_operador, db_session
):
    token = create_access_token(usuario_operador.id, {"rol": "Administrador"})
    h = {"Authorization": "Bearer " + token}
    assert client.get("/api/v1/auth/admin/ping", headers=h).status_code == 403
    usuario_operador.rol.nombre = "Inventado"
    db_session.commit()
    assert client.get("/api/v1/kardex/articulos", headers=h).status_code == 403


@pytest.mark.parametrize(
    "ruta",
    [
        "/analitica/entrenar",
        "/analitica-operativa/entrenar",
        "/cierres-anuales/2026",
        "/cierres-anuales/registro/1/reabrir",
        "/kardex/articulos/1/conciliacion-inicial",
        "/kardex/articulos/1/asignar-area",
        "/kardex/articulos/1/apertura",
        "/kardex/articulos/1/ajustes-operativos",
        "/kardex/movimiento-actual/1/corregir",
    ],
)
def test_operador_no_accede_a_mutaciones_administrativas(client, usuario_operador, ruta):
    r = client.post("/api/v1" + ruta, headers=cabecera(usuario_operador), json={})
    assert r.status_code == 403, (ruta, r.text)
