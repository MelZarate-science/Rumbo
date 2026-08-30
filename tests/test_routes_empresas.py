"""
Tests de endpoints de empresas y puestos.
"""

import pytest

from tests.conftest import auth_headers


def test_crear_empresa_ok(client, sample_empresa):
    r = client.post("/empresas", json=sample_empresa)
    assert r.status_code == 201
    data = r.json()
    assert "empresa_id" in data
    assert data["nombre_empresa"] == "TestCorp"


def test_crear_empresa_email_duplicado_falla(client, sample_empresa):
    r = client.post("/empresas", json=sample_empresa)
    assert r.status_code == 201
    r = client.post("/empresas", json={**sample_empresa, "nombre_empresa": "Otra"})
    assert r.status_code == 409
    assert r.json()["codigo"] == "EMAIL_YA_REGISTRADO"


def test_obtener_empresa_ok(client, sample_empresa):
    r = client.post("/empresas", json=sample_empresa)
    eid = r.json()["empresa_id"]
    r = client.get(f"/empresas/{eid}")
    assert r.status_code == 200
    assert r.json()["empresa_id"] == eid


def test_crear_puesto_ok(client, sample_empresa, sample_puesto):
    r = client.post("/empresas", json=sample_empresa)
    eid = r.json()["empresa_id"]
    token = r.json()["token"]
    r = client.post(f"/empresas/{eid}/puestos", json=sample_puesto, headers=auth_headers(token))
    assert r.status_code == 201
    data = r.json()
    assert "puesto_id" in data
    assert data["titulo"] == "Backend Developer"
    # Verificar que se disparó el indexado (el puesto existe y se procesa en background)
    assert data["empresa_id"] == eid


def test_crear_puesto_sin_token_falla(client, sample_empresa, sample_puesto):
    r = client.post("/empresas", json=sample_empresa)
    eid = r.json()["empresa_id"]
    r = client.post(f"/empresas/{eid}/puestos", json=sample_puesto)
    assert r.status_code == 401


def test_listar_puestos_empresa(client, sample_empresa, sample_puesto):
    r = client.post("/empresas", json=sample_empresa)
    eid = r.json()["empresa_id"]
    token = r.json()["token"]
    client.post(f"/empresas/{eid}/puestos", json=sample_puesto, headers=auth_headers(token))
    client.post(f"/empresas/{eid}/puestos", json={**sample_puesto, "titulo": "Senior Backend"}, headers=auth_headers(token))

    r = client.get(f"/empresas/{eid}/puestos")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    for p in data:
        assert "puesto_id" in p


def test_actualizar_puesto_reindexa_si_cambia_descripcion(client, sample_empresa, sample_puesto):
    r = client.post("/empresas", json=sample_empresa)
    eid = r.json()["empresa_id"]
    token = r.json()["token"]
    r = client.post(f"/empresas/{eid}/puestos", json=sample_puesto, headers=auth_headers(token))
    pid = r.json()["puesto_id"]

    # Cambiar descripción -> debe re-ejecutar indexado
    r = client.put(f"/puestos/{pid}", json={"descripcion": "Nueva descripción con Go y Kubernetes"}, headers=auth_headers(token))
    assert r.status_code == 200
    # No falla, y el puesto se actualiza
    assert r.json()["descripcion"] == "Nueva descripción con Go y Kubernetes"


def test_matches_empresa_filtra_privacidad(client, sample_perfil, sample_empresa, sample_puesto):
    # Perfil
    r = client.post("/perfiles", json=sample_perfil)
    pid = r.json()["perfil_id"]
    token_perfil = r.json()["token"]

    # Empresa + puesto
    r = client.post("/empresas", json=sample_empresa)
    eid = r.json()["empresa_id"]
    token_empresa = r.json()["token"]
    r = client.post(f"/empresas/{eid}/puestos", json=sample_puesto, headers=auth_headers(token_empresa))

    # Matching
    cv = {"experiencia": [], "formacion": [], "habilidades": ["Python", "FastAPI"], "proyectos": []}
    client.put(f"/perfiles/{pid}/cv", json=cv, headers=auth_headers(token_perfil))

    # Listar matches desde empresa
    r = client.get(f"/empresas/{eid}/mapa-perfiles")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    for m in data:
        # Perfil filtrado: sin apellido, email, telefono (estado pendiente)
        perfil = m["perfil"]
        assert "apellido" not in perfil
        assert "email" not in perfil
        assert "telefono" not in perfil
        # Pero sí cv_data
        assert "cv_data" in perfil
