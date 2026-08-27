"""
Pipeline de matching — secuencia fija, sin coordinador con modelo.

Este NO es un agente: es orquestación en código plano. La secuencia está
definida de antemano y ningún modelo decide el enrutamiento. Esa es una
decisión de arquitectura deliberada (patrón secuencial, no coordinador):
el flujo es determinístico, así que un coordinador con modelo agregaría
llamadas, costo y latencia sin aportar flexibilidad.

Backlog: tareas 2.7 a 2.11
"""

from agents.auditor_fit import calcular_score_y_roadmap
from services.embeddings import generar_embedding_perfil
from services.retrieval import buscar_roles_afines, buscar_puestos_de_roles
from services.firestore_client import crear


def ejecutar_pipeline_matching(perfil_id: str) -> list[str]:
    """
    Corre el matching completo para un perfil recién registrado.

    Disparado de forma asíncrona por Pub/Sub cuando se crea un perfil nuevo,
    sin ninguna acción manual del usuario.

    Returns:
        Lista de `match_id` creados.
    """
    generar_embedding_perfil(perfil_id)

    roles_ids = buscar_roles_afines(perfil_id)          # Nivel 1 — semántico
    puestos_ids = buscar_puestos_de_roles(roles_ids)    # Nivel 2 — filtro simple

    matches_creados = []
    for puesto_id in puestos_ids:
        resultado = calcular_score_y_roadmap(perfil_id, puesto_id)
        match_id = crear("matches", {
            "perfil_id": perfil_id,
            "puesto_id": puesto_id,
            "estado": "pendiente",
            **resultado,
        })
        matches_creados.append(match_id)

    return matches_creados


def ejecutar_pipeline_indexado(puesto_id: str) -> None:
    """
    Corre al cargarse un puesto nuevo: lo clasifica en un rol y extrae sus
    requisitos, dejándolo disponible para el matching.

    Backlog: tareas 2.3, 2.5, 2.6
    """
    from agents.clasificador_roles import clasificar_puesto
    from agents.extractor_requisitos import extraer_requisitos

    clasificar_puesto(puesto_id)
    extraer_requisitos(puesto_id)
