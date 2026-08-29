"""
Único punto de acceso a Gemini. Mismo principio que `firestore_client.py`:
nadie construye su propio cliente de `google.genai` en un agente — todos
usan `generar_json` / `generar_embedding_vector` de acá.

Dos formas de autenticarse, mutuamente excluyentes:
- `GEMINI_API_KEY` seteada -> Gemini Developer API (Google AI Studio, capa
  gratuita, sin billing de GCP). Esta es la que usa Rumbo: evita depender
  de crédito de GCP para el corazón agentic del producto.
- Sin `GEMINI_API_KEY` -> Vertex AI (requiere `GOOGLE_CLOUD_PROJECT` con
  billing y la API habilitada). Queda como alternativa si en algún momento
  se necesita cuota mayor a la gratuita.

Lazy a propósito: importar el módulo no toca la red ni requiere credenciales.
Variables respetadas: GEMINI_API_KEY, GOOGLE_CLOUD_PROJECT, VERTEX_AI_LOCATION,
GEMINI_MODEL_FLASH, GEMINI_MODEL_PRO, GEMINI_EMBEDDING_MODEL.
"""

import logging
import os

from pydantic import BaseModel

log = logging.getLogger(__name__)

_CLIENT = None


class GeminiError(RuntimeError):
    """Error al llamar a Gemini. El mensaje es para log, no para el frontend."""


def _client():
    global _CLIENT
    if _CLIENT is None:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            _CLIENT = genai.Client(api_key=api_key)
            log.info("Cliente Gemini inicializado (Google AI Studio, capa gratuita)")
        else:
            _CLIENT = genai.Client(
                vertexai=True,
                project=os.getenv("GOOGLE_CLOUD_PROJECT") or None,
                location=os.getenv("VERTEX_AI_LOCATION", "us-central1"),
            )
            log.info("Cliente Gemini inicializado (Vertex AI)")
    return _CLIENT


def generar_json(
    *,
    system_instruction: str,
    contents: str,
    response_schema: type[BaseModel],
    model: str | None = None,
    temperature: float = 0.0,
) -> BaseModel:
    """
    Llama a Gemini pidiendo salida estructurada según `response_schema`
    (un modelo Pydantic) y devuelve la instancia ya parseada.

    `temperature=0.0` por defecto: estas 3 llamadas son de clasificación/
    extracción/auditoría, no de generación creativa — se prioriza
    consistencia sobre variedad.
    """
    from google.genai import types

    modelo = model or os.getenv("GEMINI_MODEL_FLASH", "gemini-3.5-flash")
    try:
        respuesta = _client().models.generate_content(
            model=modelo,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=temperature,
            ),
        )
    except Exception as exc:  # noqa: BLE001 — re-empacado uniforme
        raise GeminiError(f"generar_json ({modelo}): {exc}") from exc

    if respuesta.parsed is None:
        raise GeminiError(f"generar_json ({modelo}): la respuesta no pudo parsearse como {response_schema.__name__}")
    return respuesta.parsed


def generar_embedding_vector(texto: str, *, model: str | None = None) -> list[float]:
    """Devuelve el vector de embedding de `texto`. Lista vacía si `texto` está vacío."""
    if not texto or not texto.strip():
        return []

    modelo = model or os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    try:
        respuesta = _client().models.embed_content(model=modelo, contents=texto)
    except Exception as exc:  # noqa: BLE001
        raise GeminiError(f"generar_embedding_vector ({modelo}): {exc}") from exc

    embeddings = respuesta.embeddings
    if not embeddings:
        raise GeminiError(f"generar_embedding_vector ({modelo}): respuesta sin embeddings")
    return list(embeddings[0].values)
