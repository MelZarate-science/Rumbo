"""
Tests de endpoints de matches: invitación y respuesta con visibilidad escalonada.
"""

import pytest


def _setup_match(client, sample_perfil, sample_empresa, sample_puesto):
    """Helper: crea perfil, empresa, puesto, dispara matching, devuelve match_id."""
    r = client.post("/perfiles", json=sample_perfil)
    pid = r.json()["perfil_id"]

    r = client.post("/empresas", json=sample_empresa)
    eid = r.json()["empresa_id"]

    r = client.post(f"/empresas/{eid}/puestos", json=sample_puesto)

    cv = {"experiencia": [], "formacion": [], "habilidades": ["Python", "FastAPI"], "proyectos": []}
    r = client.put(f"/perfiles/{pid}/cv", json=cv)
    matches = r.json()["matches_creados"]
    assert matches
    return matches[0], pid, eid


def test_obtener_match_visibilidad_empresa(client, sample_perfil, sample_empresa, sample_puesto):
    match_id, _, _ = _setup_match(client, sample_perfil, sample_empresa, sample_puesto)

    r = client.get(f"/matches/{match_id}")
    assert r.status_code == 200
    data = r.json()
    # Empresa ve empresa completa y perfil filtrado (pendiente -> sin campos privados)
    assert "empresa" in data
    assert data["empresa"]["nombre"] == "TestCorp"
    assert "perfil" in data
    assert "apellido" not in data["perfil"]
    assert "email" not in data["perfil"]
    assert "telefono" not in data["perfil"]


def test_obtener_match_visibilidad_perfil_oculta_empresa_pendiente(client, sample_perfil, sample_empresa, sample_puesto):
    match_id, _, _ = _setup_match(client, sample_perfil, sample_empresa, sample_puesto)

    r = client.get(f"/matches/{match_id}")
    assert r.status_code == 200
    data = r.json()
    # empresa_para_perfil oculta nombre en pendiente
    assert data["empresa_para_perfil"]["nombre"] is None


def test_invitar_match_ok(client, sample_perfil, sample_empresa, sample_puesto):
    match_id, _, _ = _setup_match(client, sample_perfil, sample_empresa, sample_puesto)

    r = client.post(f"/matches/{match_id}/invitar")
    assert r.status_code == 200
    assert r.json()["estado"] == "notificado"


def test_invitar_match_no_pendiente_falla(client, sample_perfil, sample_empresa, sample_puesto):
    match_id, _, _ = _setup_match(client, sample_perfil, sample_empresa, sample_puesto)

    # Invitar una vez
    client.post(f"/matches/{match_id}/invitar")
    # Segunda vez debe fallar
    r = client.post(f"/matches/{match_id}/invitar")
    assert r.status_code == 400
    assert r.json()["codigo"] == "TRANSICION_INVALIDA"


def test_responder_match_aceptar_confirma(client, sample_perfil, sample_empresa, sample_puesto):
    match_id, _, _ = _setup_match(client, sample_perfil, sample_empresa, sample_puesto)

    # Invitar primero
    client.post(f"/matches/{match_id}/invitar")
    # Responder aceptando
    r = client.post(f"/matches/{match_id}/responder", json={"aceptar": True})
    assert r.status_code == 200
    assert r.json()["estado"] == "confirmado"


def test_responder_match_rechazar(client, sample_perfil, sample_empresa, sample_puesto):
    match_id, _, _ = _setup_match(client, sample_perfil, sample_empresa, sample_puesto)

    client.post(f"/matches/{match_id}/invitar")
    r = client.post(f"/matches/{match_id}/responder", json={"aceptar": False})
    assert r.status_code == 200
    assert r.json()["estado"] == "rechazado"


def test_responder_sin_invitar_falla(client, sample_perfil, sample_empresa, sample_puesto):
    match_id, _, _ = _setup_match(client, sample_perfil, sample_empresa, sample_puesto)

    r = client.post(f"/matches/{match_id}/responder", json={"aceptar": True})
    assert r.status_code == 400
    assert r.json()["codigo"] == "TRANSICION_INVALIDA"


def test_visibilidad_perfil_confirmado_expone_privados(client, sample_perfil, sample_empresa, sample_puesto):
    match_id, _, _ = _setup_match(client, sample_perfil, sample_empresa, sample_puesto)

    client.post(f"/matches/{match_id}/invitar")
    client.post(f"/matches/{match_id}/responder", json={"aceptar": True})

    # Ahora GET /matches/{id} debe mostrar campos privados
    r = client.get(f"/matches/{match_id}")
    assert r.status_code == 200
    data = r.json()
    perfil = data["perfil"]
    assert perfil["apellido"] == "User"
    assert perfil["email"] == "test@example.com"
    assert perfil["telefono"] == "+34 600 123 456"


def test_responder_body_invalido(client, sample_perfil, sample_empresa, sample_puesto):
    match_id, _, _ = _setup_match(client, sample_perfil, sample_empresa, sample_puesto)
    client.post(f"/matches/{match_id}/invitar")

    r = client.post(f"/matches/{match_id}/responder", json={})
    assert r.status_code == 422
    assert r.json()["codigo"] == "ERROR_VALIDACION"