"""
Tests de autenticación (backlog 1.1).
"""

from tests.conftest import auth_headers_for, registrar_empresa, registrar_perfil


def test_login_perfil_ok(client, sample_perfil):
    client.cookies.clear()
    registrar_perfil(client, sample_perfil)
    client.post("/auth/logout")
    r = client.post("/auth/login", json={"email": sample_perfil["email"], "password": sample_perfil["password"], "tipo": "perfil"})
    assert r.status_code == 200
    data = r.json()
    assert data["tipo"] == "perfil"
    assert "token" not in data
    assert "rumbo_session=" in r.headers["set-cookie"]


def test_login_perfil_password_incorrecta(client, sample_perfil):
    registrar_perfil(client, sample_perfil)
    client.post("/auth/logout")
    r = client.post("/auth/login", json={"email": sample_perfil["email"], "password": "otra-cosa", "tipo": "perfil"})
    assert r.status_code == 401
    assert r.json()["codigo"] == "CREDENCIALES_INVALIDAS"


def test_login_email_no_existe(client):
    r = client.post("/auth/login", json={"email": "no-existe@test.com", "password": "cualquiera", "tipo": "perfil"})
    assert r.status_code == 401


def test_login_empresa_ok(client, sample_empresa):
    registrar_empresa(client, sample_empresa)
    client.post("/auth/logout")
    r = client.post("/auth/login", json={"email": sample_empresa["email_registro"], "password": sample_empresa["password"], "tipo": "empresa"})
    assert r.status_code == 200
    assert r.json()["tipo"] == "empresa"


def test_crear_perfil_devuelve_token_y_oculta_password_hash(client, sample_perfil):
    r = client.post("/perfiles", json=sample_perfil)
    data = r.json()
    assert data["tipo"] == "perfil"
    assert "token" not in data
    assert "password_hash" not in data
    assert "password" not in data
    assert "rumbo_session=" in r.headers["set-cookie"]


def test_crear_empresa_devuelve_token_y_oculta_password_hash(client, sample_empresa):
    r = client.post("/empresas", json=sample_empresa)
    data = r.json()
    assert data["tipo"] == "empresa"
    assert "token" not in data
    assert "password_hash" not in data
    assert "password" not in data
    assert "rumbo_session=" in r.headers["set-cookie"]


def test_session_devuelve_usuario_actual(client, sample_perfil):
    r = client.post("/perfiles", json=sample_perfil)
    perfil_id = r.json()["perfil_id"]

    r = client.get("/auth/session")
    assert r.status_code == 200
    assert r.json() == {"id": perfil_id, "tipo": "perfil"}


def test_logout_limpia_cookie(client, sample_perfil):
    registrar_perfil(client, sample_perfil)
    r = client.post("/auth/logout")
    assert r.status_code == 200
    assert "rumbo_session=" in r.headers["set-cookie"]
    r = client.get("/auth/session")
    assert r.status_code == 401


def test_session_acepta_fallback_bearer(client, sample_perfil):
    perfil_id = registrar_perfil(client, sample_perfil)
    client.cookies.clear()

    r = client.get("/auth/session", headers=auth_headers_for(perfil_id, "perfil"))
    assert r.status_code == 200
    assert r.json() == {"id": perfil_id, "tipo": "perfil"}


def test_login_rate_limit_por_mismo_email(client, sample_perfil):
    registrar_perfil(client, sample_perfil)
    client.post("/auth/logout")

    for _ in range(10):
        r = client.post(
            "/auth/login",
            json={"email": sample_perfil["email"], "password": "otra-cosa", "tipo": "perfil"},
        )
        assert r.status_code == 401

    r = client.post(
        "/auth/login",
        json={"email": sample_perfil["email"], "password": "otra-cosa", "tipo": "perfil"},
    )
    assert r.status_code == 429
    assert r.json()["codigo"] == "RATE_LIMIT_EXCEDIDO"


def test_login_rate_limit_por_ip_con_emails_distintos(client):
    for index in range(10):
        r = client.post(
            "/auth/login",
            json={"email": f"no-existe-{index}@test.com", "password": "password123", "tipo": "perfil"},
        )
        assert r.status_code == 401

    r = client.post(
        "/auth/login",
        json={"email": "no-existe-final@test.com", "password": "password123", "tipo": "perfil"},
    )
    assert r.status_code == 429
    assert r.json()["codigo"] == "RATE_LIMIT_EXCEDIDO"
