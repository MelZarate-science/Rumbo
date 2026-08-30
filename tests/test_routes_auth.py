"""
Tests de autenticación (backlog 1.1).
"""


def test_login_perfil_ok(client, sample_perfil):
    client.post("/perfiles", json=sample_perfil)
    r = client.post("/auth/login", json={"email": sample_perfil["email"], "password": sample_perfil["password"], "tipo": "perfil"})
    assert r.status_code == 200
    data = r.json()
    assert data["tipo"] == "perfil"
    assert "token" in data


def test_login_perfil_password_incorrecta(client, sample_perfil):
    client.post("/perfiles", json=sample_perfil)
    r = client.post("/auth/login", json={"email": sample_perfil["email"], "password": "otra-cosa", "tipo": "perfil"})
    assert r.status_code == 401
    assert r.json()["codigo"] == "CREDENCIALES_INVALIDAS"


def test_login_email_no_existe(client):
    r = client.post("/auth/login", json={"email": "no-existe@test.com", "password": "cualquiera", "tipo": "perfil"})
    assert r.status_code == 401


def test_login_empresa_ok(client, sample_empresa):
    client.post("/empresas", json=sample_empresa)
    r = client.post("/auth/login", json={"email": sample_empresa["email_registro"], "password": sample_empresa["password"], "tipo": "empresa"})
    assert r.status_code == 200
    assert r.json()["tipo"] == "empresa"


def test_crear_perfil_devuelve_token_y_oculta_password_hash(client, sample_perfil):
    r = client.post("/perfiles", json=sample_perfil)
    data = r.json()
    assert "token" in data
    assert "password_hash" not in data
    assert "password" not in data


def test_crear_empresa_devuelve_token_y_oculta_password_hash(client, sample_empresa):
    r = client.post("/empresas", json=sample_empresa)
    data = r.json()
    assert "token" in data
    assert "password_hash" not in data
    assert "password" not in data
