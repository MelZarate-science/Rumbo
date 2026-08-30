"""
Tests de endpoints de matches: invitación y respuesta con visibilidad escalonada.
"""

from tests.conftest import auth_headers_for, registrar_empresa, registrar_perfil


def _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto):
    """Crea ambos actores con sus cookies y devuelve `(match_id, perfil_id, empresa_id)`."""
    pid = registrar_perfil(perfil_client, sample_perfil)
    eid = registrar_empresa(empresa_client, sample_empresa)

    r = empresa_client.post(f"/empresas/{eid}/puestos", json=sample_puesto)
    assert r.status_code == 201

    cv = {"experiencia": [], "formacion": [], "habilidades": ["Python", "FastAPI"], "proyectos": []}
    r = perfil_client.put(f"/perfiles/{pid}/cv", json=cv)
    matches = r.json()["matches_creados"]
    assert matches
    return matches[0], pid, eid


def test_obtener_match_visibilidad_empresa(make_client, sample_perfil, sample_empresa, sample_puesto):
    perfil_client = make_client()
    empresa_client = make_client()
    try:
        match_id, _, _ = _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto)
        r = empresa_client.get(f"/matches/{match_id}")
        assert r.status_code == 200
        data = r.json()
        assert "empresa" in data
        assert data["empresa"]["nombre"] == "TestCorp"
        assert "perfil" in data
        assert "apellido" not in data["perfil"]
        assert "email" not in data["perfil"]
        assert "telefono" not in data["perfil"]
    finally:
        perfil_client.close()
        empresa_client.close()


def test_obtener_match_visibilidad_perfil_oculta_empresa_pendiente(make_client, sample_perfil, sample_empresa, sample_puesto):
    perfil_client = make_client()
    empresa_client = make_client()
    try:
        match_id, _, _ = _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto)
        r = perfil_client.get(f"/matches/{match_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["empresa_para_perfil"]["nombre"] is None
    finally:
        perfil_client.close()
        empresa_client.close()


def test_invitar_match_ok(make_client, sample_perfil, sample_empresa, sample_puesto):
    perfil_client = make_client()
    empresa_client = make_client()
    try:
        match_id, _, _ = _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto)
        r = empresa_client.post(f"/matches/{match_id}/invitar")
        assert r.status_code == 200
        assert r.json()["estado"] == "notificado"
    finally:
        perfil_client.close()
        empresa_client.close()


def test_invitar_match_sin_token_falla(make_client, sample_perfil, sample_empresa, sample_puesto):
    perfil_client = make_client()
    empresa_client = make_client()
    anon_client = make_client()
    try:
        match_id, _, _ = _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto)
        r = anon_client.post(f"/matches/{match_id}/invitar")
        assert r.status_code == 401
    finally:
        perfil_client.close()
        empresa_client.close()
        anon_client.close()


def test_invitar_match_no_pendiente_falla(make_client, sample_perfil, sample_empresa, sample_puesto):
    perfil_client = make_client()
    empresa_client = make_client()
    try:
        match_id, _, _ = _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto)
        empresa_client.post(f"/matches/{match_id}/invitar")
        r = empresa_client.post(f"/matches/{match_id}/invitar")
        assert r.status_code == 400
        assert r.json()["codigo"] == "TRANSICION_INVALIDA"
    finally:
        perfil_client.close()
        empresa_client.close()


def test_responder_match_aceptar_confirma(make_client, sample_perfil, sample_empresa, sample_puesto):
    perfil_client = make_client()
    empresa_client = make_client()
    try:
        match_id, _, _ = _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto)
        empresa_client.post(f"/matches/{match_id}/invitar")
        r = perfil_client.post(f"/matches/{match_id}/responder", json={"aceptar": True})
        assert r.status_code == 200
        assert r.json()["estado"] == "confirmado"
    finally:
        perfil_client.close()
        empresa_client.close()


def test_responder_match_rechazar(make_client, sample_perfil, sample_empresa, sample_puesto):
    perfil_client = make_client()
    empresa_client = make_client()
    try:
        match_id, _, _ = _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto)
        empresa_client.post(f"/matches/{match_id}/invitar")
        r = perfil_client.post(f"/matches/{match_id}/responder", json={"aceptar": False})
        assert r.status_code == 200
        assert r.json()["estado"] == "rechazado"
    finally:
        perfil_client.close()
        empresa_client.close()


def test_responder_sin_invitar_falla(make_client, sample_perfil, sample_empresa, sample_puesto):
    perfil_client = make_client()
    empresa_client = make_client()
    try:
        match_id, _, _ = _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto)
        r = perfil_client.post(f"/matches/{match_id}/responder", json={"aceptar": True})
        assert r.status_code == 400
        assert r.json()["codigo"] == "TRANSICION_INVALIDA"
    finally:
        perfil_client.close()
        empresa_client.close()


def test_visibilidad_perfil_confirmado_expone_privados(make_client, sample_perfil, sample_empresa, sample_puesto):
    perfil_client = make_client()
    empresa_client = make_client()
    try:
        match_id, _, _ = _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto)
        empresa_client.post(f"/matches/{match_id}/invitar")
        perfil_client.post(f"/matches/{match_id}/responder", json={"aceptar": True})
        r = empresa_client.get(f"/matches/{match_id}")
        assert r.status_code == 200
        data = r.json()
        perfil = data["perfil"]
        assert perfil["apellido"] == "User"
        assert perfil["email"] == "test@example.com"
        assert perfil["telefono"] == "+34 600 123 456"
    finally:
        perfil_client.close()
        empresa_client.close()


def test_responder_body_invalido(make_client, sample_perfil, sample_empresa, sample_puesto):
    perfil_client = make_client()
    empresa_client = make_client()
    try:
        match_id, _, _ = _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto)
        empresa_client.post(f"/matches/{match_id}/invitar")
        r = perfil_client.post(f"/matches/{match_id}/responder", json={})
        assert r.status_code == 422
        assert r.json()["codigo"] == "ERROR_VALIDACION"
    finally:
        perfil_client.close()
        empresa_client.close()


def test_obtener_match_sin_sesion_falla(make_client, sample_perfil, sample_empresa, sample_puesto):
    perfil_client = make_client()
    empresa_client = make_client()
    anon_client = make_client()
    try:
        match_id, _, _ = _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto)
        r = anon_client.get(f"/matches/{match_id}")
        assert r.status_code == 401
    finally:
        perfil_client.close()
        empresa_client.close()
        anon_client.close()


def test_obtener_match_de_tercero_falla(make_client, sample_perfil, sample_empresa, sample_puesto):
    perfil_client = make_client()
    empresa_client = make_client()
    tercero_client = make_client()
    try:
        match_id, _, _ = _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto)
        registrar_perfil(
            tercero_client,
            {**sample_perfil, "email": "otro@test.com", "telefono": "+34 600 333 222"},
        )
        r = tercero_client.get(f"/matches/{match_id}")
        assert r.status_code == 403
    finally:
        perfil_client.close()
        empresa_client.close()
        tercero_client.close()


def test_obtener_match_acepta_fallback_bearer(make_client, sample_perfil, sample_empresa, sample_puesto):
    perfil_client = make_client()
    empresa_client = make_client()
    try:
        match_id, _, eid = _setup_match(perfil_client, empresa_client, sample_perfil, sample_empresa, sample_puesto)
        empresa_client.cookies.clear()
        r = empresa_client.get(f"/matches/{match_id}", headers=auth_headers_for(eid, "empresa"))
        assert r.status_code == 200
    finally:
        perfil_client.close()
        empresa_client.close()
