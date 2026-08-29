"""
Agente 1 — Clasificador de roles.

Recibe un puesto recién cargado y decide, con razonamiento semántico real
(Gemini), si pertenece a un rol ya existente en `roles_normalizados` o si hay
que crear uno nuevo. Ver `agents/prompts/clasificador_roles_prompt.txt` para
el criterio completo.

Backlog: tarea 2.3
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from services import gemini_client
from services.firestore_client import actualizar, crear, listar, obtener

_PROMPT = (Path(__file__).parent / "prompts" / "clasificador_roles_prompt.txt").read_text(encoding="utf-8")


class ClasificacionRol(BaseModel):
    es_rol_nuevo: bool
    rol_existente_id: str | None
    nombre_normalizado: str
    descripcion_consolidada: str


def clasificar_puesto(puesto_id: str) -> str:
    """
    Asigna un `rol_normalizado_id` al puesto, usando el Agente 1 (Gemini).

    Args:
        puesto_id: ID del documento en la colección `puestos`.

    Returns:
        El `rol_normalizado_id` asignado (existente o recién creado).
    """
    puesto = obtener("puestos", puesto_id)
    if puesto is None:
        raise ValueError(f"puesto {puesto_id} no encontrado")

    roles = listar("roles_normalizados")
    ids_existentes = {r["_document_id"] for r in roles}

    contents = json.dumps({
        "catalogo_roles": [
            {
                "id": r["_document_id"],
                "nombre_normalizado": r.get("nombre_normalizado", ""),
                "descripcion_consolidada": r.get("descripcion_consolidada", ""),
            }
            for r in roles
        ],
        "puesto": {
            "titulo": puesto.get("titulo", ""),
            "descripcion": puesto.get("descripcion", ""),
        },
    }, ensure_ascii=False)

    resultado = gemini_client.generar_json(
        system_instruction=_PROMPT,
        contents=contents,
        response_schema=ClasificacionRol,
    )

    if not resultado.es_rol_nuevo and resultado.rol_existente_id in ids_existentes:
        rol_id = resultado.rol_existente_id
    else:
        rol_id = crear("roles_normalizados", {
            "nombre_normalizado": resultado.nombre_normalizado,
            "descripcion_consolidada": resultado.descripcion_consolidada,
            "requisitos_frecuencia": [],
            "requisitos_ids": [],
            "cantidad_puestos": 0,
            "updated_at": datetime.now(UTC),
        })
        from services.embeddings import generar_embedding_rol
        generar_embedding_rol(rol_id)

    actualizar("puestos", puesto_id, {"rol_normalizado_id": rol_id})
    return rol_id
