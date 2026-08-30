"""
Retrieval en dos niveles. Ninguno de los dos usa el modelo de razonamiento
— esa es justamente la decisión de arquitectura que mantiene bajo el costo.

Nivel 1: `find_nearest()` del embedding del perfil contra `roles_normalizados`.
Nivel 2: filtro simple y gratis, contra la colección grande (`puestos`).

Backlog: tareas 2.7 y 2.8
"""

import logging

from services.embeddings import generar_embedding_perfil
from services.firestore_client import buscar_vecinos, listar, obtener

log = logging.getLogger(__name__)

_UMBRAL_DISTANCIA_ROL = 0.40
"""
Distancia coseno máxima (0 = idéntico, 2 = opuesto) para considerar un rol
remotamente relevante para un perfil. Sin este piso, `find_nearest()` siempre
devolvía los `limite` roles "más cercanos" que hubiera, aunque el perfil no
tuviera nada que ver con ninguno.

Calibrado con datos reales (no adivinado): en la corrida de seed contra
Vertex AI con 6 perfiles x 6 roles, los roles genuinamente afines a cada
perfil cayeron entre 0.21 y 0.40 de distancia, y los roles claramente ajenos
(ej. "Product Management" para un perfil 100% backend) entre 0.43 y 0.48 --
un placeholder anterior de 0.6 nunca filtraba nada, porque ninguna distancia
real observada lo superaba (por eso el retrieval devolvía casi siempre los
3 roles completos para cualquier perfil). Con una muestra de solo 6 perfiles
esto es un punto de partida, no un número definitivo -- reajustar a medida
que haya más variedad real de perfiles y roles.
"""


def buscar_roles_afines(perfil_id: str, limite: int = 3) -> list[str]:
    """
    NIVEL 1 — `find_nearest()` del embedding del perfil contra el embedding
    de `roles_normalizados` (`descripcion_consolidada`).

    Si el perfil todavía no tiene embedding guardado, se genera acá (idempotente:
    llamadas siguientes ya lo encuentran guardado).

    Returns: lista de `rol_normalizado_id`, los más afines primero. Vacía si
    ninguno supera el piso mínimo de similitud (ver `_UMBRAL_DISTANCIA_ROL`).
    """
    perfil = obtener("perfiles", perfil_id)
    if not perfil:
        return []

    vector = perfil.get("embedding")
    if not vector:
        vector = generar_embedding_perfil(perfil_id)
    if not vector:
        log.warning("perfil %s sin embedding disponible; no se puede hacer retrieval nivel 1", perfil_id)
        return []

    roles = buscar_vecinos(
        "roles_normalizados", "embedding", vector, limite=limite,
        umbral_distancia=_UMBRAL_DISTANCIA_ROL,
    )
    return [r["_document_id"] for r in roles]


def buscar_puestos_de_roles(roles_ids: list[str]) -> list[str]:
    """
    NIVEL 2 — filtro simple de `puestos` por `rol_normalizado_id`.
    Sin vectores, sin LLM: es una query de Firestore.

    Returns: lista de `puesto_id` activos de esos roles.
    """
    if not roles_ids:
        return []
    puestos = listar("puestos", {"rol_normalizado_id": roles_ids, "activo": True})
    return [p["_document_id"] for p in puestos]
