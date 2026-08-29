"""
Generación de embeddings (Vertex AI, vía `services/gemini_client.py`) y
persistencia como `Vector` de Firestore, requerido para `find_nearest()`.

Backlog: tareas 2.2 y 2.4
"""

import logging

from services import gemini_client
from services.firestore_client import guardar_embedding, obtener

log = logging.getLogger(__name__)


def generar_embedding(texto: str) -> list[float]:
    """Devuelve el vector de embedding de `texto`. Lista vacía si `texto` está vacío."""
    return gemini_client.generar_embedding_vector(texto)


def _cv_texto_consolidado(perfil: dict) -> str:
    partes = []
    if perfil.get("cv_texto_original"):
        partes.append(perfil["cv_texto_original"])
    cv = perfil.get("cv_data", {}) or {}
    for exp in cv.get("experiencia", []):
        partes.append(f"{exp.get('puesto', '')}: {exp.get('descripcion', '')}")
    for form in cv.get("formacion", []):
        partes.append(form.get("descripcion") or form.get("titulo", ""))
    partes.extend(cv.get("habilidades", []))
    for proj in cv.get("proyectos", []):
        partes.append(proj.get("descripcion", ""))
    return " ".join(filter(None, partes))


def generar_embedding_perfil(perfil_id: str) -> list[float]:
    """Consolida el `cv_data` del perfil en texto, genera y guarda su embedding."""
    perfil = obtener("perfiles", perfil_id)
    if perfil is None:
        raise ValueError(f"perfil {perfil_id} no encontrado")

    texto = _cv_texto_consolidado(perfil)
    if not texto:
        log.warning("perfil %s sin contenido de cv_data; no se genera embedding", perfil_id)
        return []

    vector = gemini_client.generar_embedding_vector(texto)
    guardar_embedding("perfiles", perfil_id, "embedding", vector)
    return vector


def generar_embedding_rol(rol_normalizado_id: str) -> list[float]:
    """Genera y guarda el embedding de `descripcion_consolidada` del rol."""
    rol = obtener("roles_normalizados", rol_normalizado_id)
    if rol is None:
        raise ValueError(f"rol {rol_normalizado_id} no encontrado")

    texto = rol.get("descripcion_consolidada", "")
    if not texto:
        log.warning("rol %s sin descripcion_consolidada; no se genera embedding", rol_normalizado_id)
        return []

    vector = gemini_client.generar_embedding_vector(texto)
    guardar_embedding("roles_normalizados", rol_normalizado_id, "embedding", vector)
    return vector
