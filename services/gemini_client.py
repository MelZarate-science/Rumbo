"""
Único punto de acceso a Gemini. Mismo principio que `firestore_client.py`:
nadie construye su propio cliente/agente en un archivo de agents/ — todos
usan `generar_json` / `generar_embedding_vector` de acá.

Backend: Vertex AI (Google Cloud), no la capa gratuita de Google AI Studio —
así el consumo corre contra el proyecto de GCP y su crédito, como pide la
competencia y refleja el diagrama de arquitectura. Requiere:
- GOOGLE_CLOUD_PROJECT + GOOGLE_CLOUD_LOCATION (o VERTEX_AI_LOCATION)
- GOOGLE_GENAI_USE_VERTEXAI=True
- Vertex AI API habilitada y billing en el proyecto
- Credenciales ADC (`gcloud auth application-default login`) o Secret
  Manager en Cloud Run.

`generar_json` corre los 3 agentes (clasificador, extractor, auditor) con
el framework Google ADK (Runner + sesión in-memory) — es el requisito de
la competencia, no una implementación directa del SDK de Gemini.
`generar_embedding_vector` NO usa ADK: los embeddings no son razonamiento
de un agente (ver rumbo-contrato-interfaces.md), son una transformación
mecánica — alcanza con una llamada directa al cliente de Vertex AI.

Lazy a propósito: importar el módulo no toca la red ni requiere credenciales.
"""

import asyncio
import logging
import os
import time
import uuid

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
    modelo) con backoff exponencial corto.
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
    """Cliente crudo de google-genai, usado solo para embeddings (no razonamiento)."""
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
                location=os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("VERTEX_AI_LOCATION", "us-central1"),
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
    Corre uno de los 3 agentes (Google ADK, Runner + sesión in-memory) y
    devuelve la respuesta ya parseada como el modelo Pydantic de `response_schema`.

    `temperature=0.0` por defecto: estas 3 llamadas son de clasificación/
    extracción/auditoría, no de generación creativa — se prioriza
    consistencia sobre variedad.
    """
    modelo = model or os.getenv("GEMINI_MODEL_FLASH", "gemini-2.5-flash")
    try:
        texto = _con_reintentos(
            lambda: asyncio.run(_ejecutar_agente_adk(modelo, system_instruction, contents, response_schema, temperature)),
            etiqueta=f"generar_json ({modelo})",
        )
    except Exception as exc:  # noqa: BLE001 — re-empacado uniforme
        raise GeminiError(f"generar_json ({modelo}): {exc}") from exc

    if texto is None:
        raise GeminiError(f"generar_json ({modelo}): ADK no devolvió una respuesta final")
    try:
        return response_schema.model_validate_json(texto)
    except Exception as exc:  # noqa: BLE001
        raise GeminiError(f"generar_json ({modelo}): la respuesta no pudo parsearse como {response_schema.__name__}: {exc}") from exc


async def _ejecutar_agente_adk(
    modelo: str,
    system_instruction: str,
    contents: str,
    response_schema: type[BaseModel],
    temperature: float,
) -> str | None:
    from google.adk.agents import LlmAgent
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    agent = LlmAgent(
        name="rumbo_agent",
        model=modelo,
        instruction=system_instruction,
        output_schema=response_schema,
        generate_content_config=types.GenerateContentConfig(temperature=temperature),
    )
    runner = InMemoryRunner(agent=agent, app_name="rumbo")
    user_id = "rumbo"
    session_id = uuid.uuid4().hex

    await runner.session_service.create_session(app_name="rumbo", user_id=user_id, session_id=session_id)

    texto_final = None
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=contents)]),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            texto_final = event.content.parts[0].text

    await runner.close()
    return texto_final


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
