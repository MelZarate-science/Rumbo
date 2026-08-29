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
import time

from pydantic import BaseModel

log = logging.getLogger(__name__)

_CLIENT = None
_REINTENTOS = 5
_ESPERA_BASE_SEGUNDOS = 3


class GeminiError(RuntimeError):
    """Error al llamar a Gemini. El mensaje es para log, no para el frontend."""


def _con_reintentos(fn, *, etiqueta: str):
    """
    Reintenta `fn()` ante `ServerError` (503, sobrecarga transitoria del
    modelo) con backoff exponencial corto. La capa gratuita de AI Studio
    sufre picos de demanda con más frecuencia que un plan pago — esto no
    es hipotético, se observó en uso real corriendo el seed data.
    """
    from google.genai import errors

    ultimo_error = None
    for intento in range(1, _REINTENTOS + 1):
        try:
            return fn()
        except errors.ServerError as exc:
            ultimo_error = exc
            if intento == _REINTENTOS:
                break
            espera = _ESPERA_BASE_SEGUNDOS * (2 ** (intento - 1))
            log.warning("%s: intento %d/%d falló (%s), reintentando en %ds", etiqueta, intento, _REINTENTOS, exc, espera)
            time.sleep(espera)
    raise ultimo_error


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

    modelo = model or os.getenv("GEMINI_MODEL_FLASH", "gemini-3.5-flash-lite")
    try:
        respuesta = _con_reintentos(
            lambda: _client().models.generate_content(
                model=modelo,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=temperature,
                ),
            ),
            etiqueta=f"generar_json ({modelo})",
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

    from google.genai import types

    modelo = model or os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    # Firestore permite vectores de hasta 2048 dimensiones (find_nearest());
    # gemini-embedding-001 devuelve 3072 por defecto, hay que pedirle menos.
    try:
        respuesta = _con_reintentos(
            lambda: _client().models.embed_content(
                model=modelo,
                contents=texto,
                config=types.EmbedContentConfig(output_dimensionality=1536),
            ),
            etiqueta=f"generar_embedding_vector ({modelo})",
        )
    except Exception as exc:  # noqa: BLE001
        raise GeminiError(f"generar_embedding_vector ({modelo}): {exc}") from exc

    embeddings = respuesta.embeddings
    if not embeddings:
        raise GeminiError(f"generar_embedding_vector ({modelo}): respuesta sin embeddings")
    return list(embeddings[0].values)
