"""
Agente 2 — Extractor de requisitos.

Descompone la descripción en texto libre de un puesto en requisitos discretos,
reconciliándolos con razonamiento semántico real (Gemini) contra
`requisitos_normalizados` (reconoce que "manejo de bases de datos" y "SQL" son
la misma entidad). Ver `agents/prompts/extractor_requisitos_prompt.txt`.

Backlog: tareas 2.5 y 2.6
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from services import gemini_client
from services.firestore_client import actualizar, crear, listar, obtener

_PROMPT = (Path(__file__).parent / "prompts" / "extractor_requisitos_prompt.txt").read_text(encoding="utf-8")

_TIPOS_VALIDOS = {"herramienta", "habilidad_blanda", "certificacion"}


class RequisitoDetectado(BaseModel):
    requisito_existente_id: str | None
    nombre: str
    tipo: str | None


class ExtraccionRequisitos(BaseModel):
    requisitos: list[RequisitoDetectado]


def extraer_requisitos(puesto_id: str) -> tuple[list[str], set[str]]:
    """
    Extrae los requisitos del puesto (Agente 2, Gemini) y los reconcilia
    contra el catálogo existente.

    Args:
        puesto_id: ID del documento en la colección `puestos`.

    Returns:
        Tupla (lista de `requisito_id`, set de `requisito_id` creados nuevos).
    """
    puesto = obtener("puestos", puesto_id)
    if puesto is None:
        raise ValueError(f"puesto {puesto_id} no encontrado")

    catalogo = listar("requisitos_normalizados")
    ids_existentes = {r["_document_id"] for r in catalogo}

    contents = json.dumps({
        "catalogo_requisitos": [
            {"id": r["_document_id"], "nombre": r.get("nombre", ""), "tipo": r.get("tipo", "")}
            for r in catalogo
        ],
        "puesto": {
            "titulo": puesto.get("titulo", ""),
            "descripcion": puesto.get("descripcion", ""),
        },
    }, ensure_ascii=False)

    resultado = gemini_client.generar_json(
        system_instruction=_PROMPT,
        contents=contents,
        response_schema=ExtraccionRequisitos,
    )

    requisitos_encontrados: list[str] = []
    nuevos_requisitos: set[str] = set()
    vistos: set[str] = set()

    for item in resultado.requisitos:
        if item.requisito_existente_id and item.requisito_existente_id in ids_existentes:
            req_id = item.requisito_existente_id
        else:
            tipo = item.tipo if item.tipo in _TIPOS_VALIDOS else "herramienta"
            req_id = crear("requisitos_normalizados", {
                "nombre": item.nombre, "tipo": tipo, "created_at": datetime.now(UTC),
            })
            nuevos_requisitos.add(req_id)

        if req_id in vistos:
            continue
        vistos.add(req_id)
        requisitos_encontrados.append(req_id)

    actualizar("puestos", puesto_id, {"requisitos_extraidos": requisitos_encontrados})

    # Frecuencias del rol: se actualizan en pipeline/indexado, no acá (idempotencia).
    return requisitos_encontrados, nuevos_requisitos
