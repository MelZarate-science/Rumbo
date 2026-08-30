"""
Configuración de tests: Fake Firestore + TestClient de FastAPI.
"""

import os

os.environ.setdefault("AUTH_SECRET_KEY", "clave-de-test-no-usar-en-produccion")

import pytest
from fastapi.testclient import TestClient

# Monkey-patch del cliente Firestore ANTES de importar main
import services.firestore_client as fc
from tests.fakes import FAKE_DB, FakeFirestore

# Monkey-patch de Gemini: los tests nunca llaman a la API real (sin red, sin
# credenciales). Ver `tests/fakes_gemini.py` para el criterio del doble de prueba.
import services.gemini_client as gc
from tests.fakes_gemini import fake_generar_embedding_vector, fake_generar_json


def _fake_client():
    return FAKE_DB


fc._client = _fake_client
fc._CLIENT = FAKE_DB  # type: ignore

gc.generar_json = fake_generar_json
gc.generar_embedding_vector = fake_generar_embedding_vector

# El umbral de similitud de `buscar_roles_afines` está calibrado contra la
# escala de distancia de embeddings REALES (ver services/retrieval.py) -- el
# fake de embeddings de arriba es un hash de bag-of-words con una escala de
# distancia totalmente distinta (todo o nada, no la variación continua de un
# embedding real), así que aplicar ese mismo número acá filtraría de más o de
# menos sin que signifique nada. Se desactiva para tests, mismo criterio que
# reemplazar Gemini/Firestore por dobles de prueba.
import services.retrieval as retrieval_module
retrieval_module._UMBRAL_DISTANCIA_ROL = None

# Ahora importamos la app (que importa routes, que importan firestore_client)
from main import app


@pytest.fixture(autouse=True)
def fake_db():
    """Fixture que limpia el fake DB antes de cada test."""
    FAKE_DB.clear_all()
    yield FAKE_DB
    FAKE_DB.clear_all()


@pytest.fixture
def client():
    """TestClient de FastAPI con el fake DB ya inyectado."""
    return TestClient(app)


@pytest.fixture
def sample_perfil():
    """Datos mínimos válidos de un perfil para tests."""
    return {
        "nombre": "Test",
        "apellido": "User",
        "email": "test@example.com",
        "password": "password123",
        "telefono": "+34 600 123 456",
        "cv_texto_original": "Experiencia en Python y FastAPI.",
        "cv_data": {
            "experiencia": [],
            "formacion": [],
            "habilidades": ["Python", "FastAPI"],
            "proyectos": [],
        },
        "busqueda_interes": "Backend",
    }


@pytest.fixture
def sample_empresa():
    return {
        "nombre_empresa": "TestCorp",
        "contexto": "Empresa de test para validar endpoints.",
        "email_registro": "hr@testcorp.com",
        "password": "password123",
    }


def auth_headers(token: str) -> dict:
    """Header Authorization listo para pasar a `client.put/post(..., headers=...)`."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_puesto():
    return {
        "titulo": "Backend Developer",
        "descripcion": "Python, FastAPI, PostgreSQL, Docker. 3+ años.",
    }