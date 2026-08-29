"""
Configuración de tests: Fake Firestore + TestClient de FastAPI.
"""

import pytest
from fastapi.testclient import TestClient

# Monkey-patch del cliente Firestore ANTES de importar main
import services.firestore_client as fc
from tests.fakes import FAKE_DB, FakeFirestore

# Guardar referencias originales
_original_client_getter = fc._client


def _fake_client():
    return FAKE_DB


fc._client = _fake_client
fc._CLIENT = FAKE_DB  # type: ignore

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
    }


@pytest.fixture
def sample_puesto():
    return {
        "titulo": "Backend Developer",
        "descripcion": "Python, FastAPI, PostgreSQL, Docker. 3+ años.",
    }