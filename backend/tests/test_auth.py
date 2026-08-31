def test_login_correcto_devuelve_token(client, usuario_admin):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Password123!"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_password_incorrecto_devuelve_401(client, usuario_admin):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "clave-incorrecta"},
    )
    assert resp.status_code == 401


def test_endpoint_protegido_sin_token_devuelve_401(client):
    resp = client.get("/api/v1/auth/admin/ping")
    assert resp.status_code == 401


def test_administrador_accede_a_endpoint_admin(client, usuario_admin):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Password123!"},
    )
    token = login.json()["access_token"]

    resp = client.get(
        "/api/v1/auth/admin/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_operador_recibe_403_en_endpoint_admin(client, usuario_operador):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "operador@test.com", "password": "Password123!"},
    )
    token = login.json()["access_token"]

    resp = client.get(
        "/api/v1/auth/admin/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
