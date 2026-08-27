"""
Retrieval en dos niveles. NINGUNO de los dos usa el modelo de razonamiento —
esa es justamente la decisión de arquitectura que mantiene bajo el costo.

Nivel 1: búsqueda semántica cara, pero contra una colección chica (roles).
Nivel 2: filtro simple y gratis, contra la colección grande (puestos).

Backlog: tareas 2.7 y 2.8
"""


def buscar_roles_afines(perfil_id: str, limite: int = 3) -> list[str]:
    """
    NIVEL 1 — find_nearest() del embedding del perfil contra roles_normalizados.

    Returns: lista de `rol_normalizado_id`, los más afines primero.
    """
    raise NotImplementedError


def buscar_puestos_de_roles(roles_ids: list[str]) -> list[str]:
    """
    NIVEL 2 — filtro simple de `puestos` por `rol_normalizado_id`.
    Sin vectores, sin LLM: es una query de Firestore.

    Returns: lista de `puesto_id` activos de esos roles.
    """
    raise NotImplementedError
