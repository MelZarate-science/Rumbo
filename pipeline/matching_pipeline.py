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
from agents.clasificador_roles import clasificar_puesto
from agents.extractor_requisitos import extraer_requisitos
from services.firestore_client import crear, obtener
from services.retrieval import buscar_puestos_de_roles, buscar_roles_afines


def ejecutar_pipeline_matching(perfil_id: str) -> list[str]:
    """
    Corre el matching completo para un perfil recién registrado (o con CV actualizado).

    Disparado de forma síncrona desde la ruta PUT /perfiles/{id}/cv.
    (Pub/Sub está diferido — ver backend.md Fase 1).

    Returns:
        Lista de `match_id` creados.
    """
    roles_ids = buscar_roles_afines(perfil_id)          # Nivel 1 — token-overlap
    puestos_ids = buscar_puestos_de_roles(roles_ids)    # Nivel 2 — filtro simple

    matches_creados = []
    for puesto_id in puestos_ids:
        resultado = calcular_score_y_roadmap(perfil_id, puesto_id)

        # Resolver empresa_id desde el puesto para el modelo Match
        puesto = obtener("puestos", puesto_id)
        empresa_id = puesto.get("empresa_id") if puesto else None

        match_id = crear("matches", {
            "perfil_id": perfil_id,
            "empresa_id": empresa_id,
            "puesto_id": puesto_id,
            "score": resultado["score"],
            "roadmap": resultado["roadmap"],
            "justificacion": resultado["justificacion"],
            "estado": "pendiente",
        })
        matches_creados.append(match_id)

    return matches_creados


def ejecutar_pipeline_indexado(puesto_id: str) -> None:
    """
    Corre al cargarse un puesto nuevo: lo clasifica en un rol y extrae sus
    requisitos, dejándolo disponible para el matching.

    Backlog: tareas 2.3, 2.5, 2.6
    """
    clasificar_puesto(puesto_id)
    req_ids, nuevos = extraer_requisitos(puesto_id)
    # Guardar cuáles requisitos son nuevos para que el auditor los marque como específicos
    if nuevos:
        from services.firestore_client import actualizar
        actualizar("puestos", puesto_id, {"requisitos_nuevos": list(nuevos)})