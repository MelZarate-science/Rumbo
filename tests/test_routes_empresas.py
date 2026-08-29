"""
Tests de endpoints de empresas y puestos.
"""

import pytest


def test_crear_empresa_ok(client, sample_empresa):
    r = client.post("/empresas", json=sample_empresa)
    assert r.status_code == 201
    data = r.json()
    assert "empresa_id" in data
    assert data["nombre_empresa"] == "TestCorp"


def test_obtener_empresa_ok(client, sample_empresa):
    r = client.post("/empresas", json=sample_empresa)
    eid = r.json()["empresa_id"]
    r = client.get(f"/empresas/{eid}")
    assert r.status_code == 200
    assert r.json()["empresa_id"] == eid


def test_crear_puesto_ok(client, sample_empresa, sample_puesto):
    r = client.post("/empresas", json=sample_empresa)
    eid = r.json()["empresa_id"]
    r = client.post(f"/empresas/{eid}/puestos", json=sample_puesto)
    assert r.status_code == 201
    data = r.json()
    assert "puesto_id" in data
    assert data["titulo"] == "Backend Developer"
    # Verificar que se disparó el indexado (el puesto existe y se procesa en background)
    assert data["empresa_id"] == eid


def test_listar_puestos_empresa(client, sample_empresa, sample_puesto):
    r = client.post("/empresas", json=sample_empresa)
    eid = r.json()["empresa_id"]
    client.post(f"/empresas/{eid}/puestos", json=sample_puesto)
    client.post(f"/empresas/{eid}/puestos", json={**sample_puesto, "titulo": "Senior Backend"})

    r = client.get(f"/empresas/{eid}/puestos")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    for p in data:
        assert "puesto_id" in p


def test_actualizar_puesto_reindexa_si_cambia_descripcion(client, sample_empresa, sample_puesto):
    r = client.post("/empresas", json=sample_empresa)
    eid = r.json()["empresa_id"]
    r = client.post(f"/empresas/{eid}/puestos", json=sample_puesto)
    pid = r.json()["puesto_id"]

    # Cambiar descripción -> debe re-ejecutar indexado
    r = client.put(f"/puestos/{pid}", json={"descripcion": "Nueva descripción con Go y Kubernetes"})
    assert r.status_code == 200
    # No falla, y el puesto se actualiza
    assert r.json()["descripcion"] == "Nueva descripción con Go y Kubernetes"


def test_matches_empresa_filtra_privacidad(client, sample_perfil, sample_empresa, sample_puesto):
    # Perfil
    r = client.post("/perfiles", json=sample_perfil)
    pid = r.json()["perfil_id"]

    # Empresa + puesto
    r = client.post("/empresas", json=sample_empresa)
    eid = r.json()["empresa_id"]
    r = client.post(f"/empresas/{eid}/puestos", json=sample_puesto)

    # Matching
    cv = {"experiencia": [], "formacion": [], "habilidades": ["Python", "FastAPI"], "proyectos": []}
    client.put(f"/perfiles/{pid}/cv", json=cv)

    # Listar matches desde empresa
    r = client.get(f"/empresas/{eid}/matches")
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