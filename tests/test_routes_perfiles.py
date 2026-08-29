"""
Tests de endpoints de perfiles.
"""

import pytest


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


def test_crear_perfil_telefono_invalido(client, sample_perfil):
    sample_perfil["telefono"] = "abc"
    r = client.post("/perfiles", json=sample_perfil)
    assert r.status_code == 422
    assert r.json()["codigo"] == "ERROR_VALIDACION"


def test_obtener_perfil_ok(client, sample_perfil):
    r = client.post("/perfiles", json=sample_perfil)
    pid = r.json()["perfil_id"]
    r = client.get(f"/perfiles/{pid}")
    assert r.status_code == 200
    assert r.json()["perfil_id"] == pid


def test_obtener_perfil_no_existe(client):
    r = client.get("/perfiles/no-existe")
    assert r.status_code == 404
    assert r.json()["codigo"] == "PERFIL_NO_ENCONTRADO"


def test_actualizar_perfil_ok(client, sample_perfil):
    r = client.post("/perfiles", json=sample_perfil)
    pid = r.json()["perfil_id"]
    r = client.put(f"/perfiles/{pid}", json={"nombre": "Nuevo", "apellido": "Nombre"})
    assert r.status_code == 200
    assert r.json()["nombre"] == "Nuevo"
    assert r.json()["apellido"] == "Nombre"
    # email no cambia
    assert r.json()["email"] == "test@example.com"


def test_actualizar_cv_dispara_matching(client, sample_perfil):
    r = client.post("/perfiles", json=sample_perfil)
    pid = r.json()["perfil_id"]

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


def test_listar_matches_perfil_oculta_empresa_pendiente(client, sample_perfil, sample_empresa, sample_puesto):
    # Crear perfil
    r = client.post("/perfiles", json=sample_perfil)
    pid = r.json()["perfil_id"]

    # Crear empresa y puesto (indexado automático)
    r = client.post("/empresas", json=sample_empresa)
    eid = r.json()["empresa_id"]
    r = client.post(f"/empresas/{eid}/puestos", json=sample_puesto)
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