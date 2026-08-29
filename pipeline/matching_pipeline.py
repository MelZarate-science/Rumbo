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
from services.embeddings import generar_embedding_perfil
from services.firestore_client import crear, obtener
from services.retrieval import buscar_puestos_de_roles, buscar_roles_afines


def ejecutar_pipeline_matching(perfil_id: str) -> list[str]:
    """
    Corre el matching completo para un perfil recién registrado (o con CV actualizado).

    Disparado de forma síncrona desde la ruta PUT /perfiles/{id}/cv.
    (Pub/Sub está diferido — backlog 2.11, prioridad 🟡).

    Returns:
        Lista de `match_id` creados (nuevos; no duplica perfil_id + puesto_id).
    """
    generar_embedding_perfil(perfil_id)                 # se regenera en cada corrida (cv_data pudo cambiar)
    roles_ids = buscar_roles_afines(perfil_id)          # Nivel 1 — find_nearest()
    puestos_ids = buscar_puestos_de_roles(roles_ids)    # Nivel 2 — filtro simple

    # Verificar matches existentes para no duplicar
    matches_existentes = set()
    from services.firestore_client import listar
    for m in listar("matches", {"perfil_id": perfil_id}):
        if m.get("puesto_id"):
            matches_existentes.add(m["puesto_id"])

    matches_creados = []
    for puesto_id in puestos_ids:
        if puesto_id in matches_existentes:
            continue  # ya existe match para este perfil+puesto

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
    Corre al cargarse un puesto nuevo o al actualizarlo: lo clasifica en un rol
    y extrae sus requisitos, actualizando las frecuencias del rol de forma idempotente.

    Backlog: tareas 2.3, 2.5, 2.6
    """
    from services.firestore_client import obtener
    puesto = obtener("puestos", puesto_id)
    if puesto is None:
        raise ValueError(f"puesto {puesto_id} no encontrado")

    # Requisitos previos para decremento en frecuencias (reindexado)
    requisitos_viejos = puesto.get("requisitos_extraidos") or []

    clasificar_puesto(puesto_id)
    req_ids, nuevos = extraer_requisitos(puesto_id)

    # Actualizar frecuencias del rol de forma idempotente
    rol_id = puesto.get("rol_normalizado_id")
    if rol_id:
        from services.normalizacion import actualizar_frecuencias
        actualizar_frecuencias(rol_id, req_ids, requisitos_viejos)

    # Guardar cuáles requisitos son nuevos para que el auditor los marque como específicos
    if nuevos:
        from services.firestore_client import actualizar
        actualizar("puestos", puesto_id, {"requisitos_nuevos": list(nuevos)})