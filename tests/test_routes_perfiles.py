"""
Tests de endpoints de perfiles.
"""

from tests.conftest import registrar_empresa, registrar_perfil


def test_crear_perfil_ok(client, sample_perfil):
    r = client.post("/perfiles", json=sample_perfil)
    assert r.status_code == 201
    data = r.json()
    assert "perfil_id" in data
    assert data["nombre"] == "Test"
    assert data["email"] == "test@example.com"


def test_crear_perfil_email_invalido(client, sample_perfil):
    sample_perfil["email"] = "no-es-email"
    r = client.post("/perfiles", json=sample_perfil)
    assert r.status_code == 422
    assert r.json()["codigo"] == "ERROR_VALIDACION"


def test_crear_perfil_email_duplicado_falla(client, sample_perfil):
    r = client.post("/perfiles", json=sample_perfil)
    assert r.status_code == 201
    r = client.post("/perfiles", json={**sample_perfil, "nombre": "Otro"})
    assert r.status_code == 409
    assert r.json()["codigo"] == "EMAIL_YA_REGISTRADO"


def test_crear_perfil_telefono_invalido(client, sample_perfil):
    sample_perfil["telefono"] = "abc"
    r = client.post("/perfiles", json=sample_perfil)
    assert r.status_code == 422
    assert r.json()["codigo"] == "ERROR_VALIDACION"


def test_obtener_perfil_ok(client, sample_perfil):
    pid = registrar_perfil(client, sample_perfil)
    r = client.get(f"/perfiles/{pid}")
    assert r.status_code == 200
    assert r.json()["perfil_id"] == pid


def test_obtener_perfil_no_existe(client):
    client.cookies.clear()
    r = client.get("/perfiles/no-existe")
    assert r.status_code == 401
    assert r.json()["codigo"] == "NO_AUTENTICADO"


def test_actualizar_perfil_ok(client, sample_perfil):
    pid = registrar_perfil(client, sample_perfil)
    r = client.put(f"/perfiles/{pid}", json={"nombre": "Nuevo", "apellido": "Nombre"})
    assert r.status_code == 200
    assert r.json()["nombre"] == "Nuevo"
    assert r.json()["apellido"] == "Nombre"
    # email no cambia
    assert r.json()["email"] == "test@example.com"


def test_actualizar_perfil_sin_token_falla(client, sample_perfil):
    pid = registrar_perfil(client, sample_perfil)
    client.cookies.clear()
    r = client.put(f"/perfiles/{pid}", json={"nombre": "Nuevo"})
    assert r.status_code == 401


def test_actualizar_cv_dispara_matching(client, sample_perfil):
    pid = registrar_perfil(client, sample_perfil)

    cv = {
        "experiencia": [],
        "formacion": [],
        "habilidades": ["Python", "FastAPI", "Docker"],
        "proyectos": [],
    }
    r = client.put(f"/perfiles/{pid}/cv", json=cv)
    assert r.status_code == 200
    data = r.json()
    assert "perfil" in data
    assert "matches_creados" in data
    assert isinstance(data["matches_creados"], list)


def test_listar_matches_perfil_oculta_empresa_pendiente(client, make_client, sample_perfil, sample_empresa, sample_puesto):
    pid = registrar_perfil(client, sample_perfil)

    empresa_client = make_client()
    try:
        eid = registrar_empresa(empresa_client, sample_empresa)
        r = empresa_client.post(f"/empresas/{eid}/puestos", json=sample_puesto)
    finally:
        empresa_client.close()
    assert r.status_code == 201

    # Actualizar CV -> matching
    cv = {
        "experiencia": [],
        "formacion": [],
        "habilidades": ["Python", "FastAPI", "PostgreSQL"],
        "proyectos": [],
    }
    r = client.put(f"/perfiles/{pid}/cv", json=cv)
    assert r.status_code == 200
    matches = r.json()["matches_creados"]
    assert len(matches) > 0

    # Listar matches del perfil
    r = client.get(f"/perfiles/{pid}/matches")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    # Estado pendiente -> no debe haber empresa_nombre
    for m in data:
        assert m["estado"] == "pendiente"
        assert m["empresa_nombre"] is None


def test_cv_fecha_rango_invalido(client, sample_perfil):
    sample_perfil["cv_data"] = {
        "experiencia": [{
            "puesto": "Dev",
            "empresa": "X",
            "descripcion": "x",
            "fecha_desde": "2023-01-01T00:00:00+00:00",
            "fecha_hasta": "2022-01-01T00:00:00+00:00",  # antes que desde
            "actual": False,
        }],
        "formacion": [],
        "habilidades": [],
        "proyectos": [],
    }
    r = client.post("/perfiles", json=sample_perfil)
    assert r.status_code == 422
    assert r.json()["codigo"] == "ERROR_VALIDACION"


def test_obtener_perfil_sin_sesion_falla(client, sample_perfil):
    pid = registrar_perfil(client, sample_perfil)

    client.cookies.clear()
    r = client.get(f"/perfiles/{pid}")
    assert r.status_code == 401


def test_listar_matches_perfil_ajeno_falla(client, make_client, sample_perfil):
    pid = registrar_perfil(client, sample_perfil)

    otro = {
        **sample_perfil,
        "email": "otro@test.com",
        "telefono": "+34 600 999 999",
    }
    otro_client = make_client()
    try:
        registrar_perfil(otro_client, otro)
        r = otro_client.get(f"/perfiles/{pid}/matches")
    finally:
        otro_client.close()
    assert r.status_code == 403


def test_obtener_perfil_no_existe_para_usuario_autenticado(client, sample_perfil):
    registrar_perfil(client, sample_perfil)
    r = client.get("/perfiles/no-existe")
    assert r.status_code == 403
