"""
Agente 2 — Extractor de requisitos.

Descompone la descripción en texto libre de un puesto en requisitos discretos
y los reconcilia contra `requisitos_normalizados`, en dos llamadas a Gemini
en vez de una sola con el catálogo entero adentro:

1. Extracción pura (paso 1): Gemini lee el puesto y devuelve candidatos, sin
   catálogo -- este paso nunca creció con el tamaño del catálogo.
2. Reconciliación en cascada, por candidato:
   - Piso 0 (gratis): match exacto por nombre normalizado.
   - Piso 1 (barato): embedding del candidato + `find_nearest()` contra
     `requisitos_normalizados`, para armar una lista corta.
   - Piso 2 (Gemini, batcheado): solo los candidatos que quedaron ambiguos
     después de los pisos anteriores se mandan juntos, en una sola llamada,
     junto con su lista corta -- nunca el catálogo entero.

Ver `Auditoria-Rumbo-Normalizacion.md` (fuera del repo) para el porqué
completo de partirlo así.

Backlog: tareas 2.5 y 2.6
"""

import json
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from backend.services import gemini_client
from backend.services.embeddings import generar_embedding, generar_embedding_requisito
from backend.services.firestore_client import actualizar, buscar_vecinos, crear, listar, obtener

_PROMPT_EXTRACCION = (Path(__file__).parent / "prompts" / "extractor_requisitos_paso1_prompt.txt").read_text(encoding="utf-8")
_PROMPT_RECONCILIACION = (Path(__file__).parent / "prompts" / "extractor_requisitos_paso2_prompt.txt").read_text(encoding="utf-8")

_TIPOS_VALIDOS = {"herramienta", "habilidad_blanda", "certificacion"}
_MAX_REQUISITOS_POR_PUESTO = 15
_LIMITE_CANDIDATOS_SHORTLIST = 5


class RequisitoExtraido(BaseModel):
    nombre: str
    tipo: str | None


class ExtraccionPura(BaseModel):
    requisitos: list[RequisitoExtraido]


class ReconciliacionRequisito(BaseModel):
    nombre_candidato: str
    requisito_existente_id: str | None


class ReconciliacionRequisitos(BaseModel):
    resultados: list[ReconciliacionRequisito]


def _normalizar(texto: str) -> str:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFKD", (texto or "").lower())
        if not unicodedata.combining(c)
    )
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes).strip()


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

    contents_extraccion = json.dumps({
        "puesto": {"titulo": puesto.get("titulo", ""), "descripcion": puesto.get("descripcion", "")},
    }, ensure_ascii=False)
    extraccion = gemini_client.generar_json(
        system_instruction=_PROMPT_EXTRACCION,
        contents=contents_extraccion,
        response_schema=ExtraccionPura,
    )
    candidatos = extraccion.requisitos[:_MAX_REQUISITOS_POR_PUESTO]

    # Catálogo local para el piso 0 (comparación en Python, nunca se lo manda a Gemini).
    catalogo = listar("requisitos_normalizados")
    por_nombre_normalizado = {_normalizar(r.get("nombre", "")): r for r in catalogo}

    requisitos_encontrados: list[str] = []
    nuevos_requisitos: set[str] = set()
    vistos: set[str] = set()
    resueltos_esta_pasada: dict[str, str] = {}  # nombre normalizado -> requisito_id, evita duplicar dentro del mismo puesto
    pendientes_reconciliacion: list[dict] = []

    def _agregar(req_id: str) -> None:
        if req_id in vistos:
            return
        vistos.add(req_id)
        requisitos_encontrados.append(req_id)

    def _crear_requisito(candidato: RequisitoExtraido) -> str:
        tipo = candidato.tipo if candidato.tipo in _TIPOS_VALIDOS else "herramienta"
        req_id = crear("requisitos_normalizados", {
            "nombre": candidato.nombre, "tipo": tipo, "created_at": datetime.now(UTC),
        })
        generar_embedding_requisito(req_id)
        return req_id

    for candidato in candidatos:
        clave = _normalizar(candidato.nombre)
        if not clave:
            continue

        # Ya resuelto por otro candidato de este mismo puesto con el mismo nombre.
        if clave in resueltos_esta_pasada:
            _agregar(resueltos_esta_pasada[clave])
            continue

        # Piso 0: match exacto por string normalizado -- gratis.
        exacto = por_nombre_normalizado.get(clave)
        if exacto:
            resueltos_esta_pasada[clave] = exacto["_document_id"]
            _agregar(exacto["_document_id"])
            continue

        # Piso 1: embedding + shortlist -- barato, sin Gemini.
        vector = generar_embedding(candidato.nombre)
        shortlist = (
            buscar_vecinos("requisitos_normalizados", "embedding", vector, limite=_LIMITE_CANDIDATOS_SHORTLIST)
            if vector else []
        )

        if not shortlist:
            # Nada remotamente parecido: es nuevo, sin ambigüedad que resolver.
            req_id = _crear_requisito(candidato)
            nuevos_requisitos.add(req_id)
            resueltos_esta_pasada[clave] = req_id
            _agregar(req_id)
            continue

        # Piso 2: queda ambiguo -- se resuelve en batch, una sola llamada para todos.
        pendientes_reconciliacion.append({"clave": clave, "candidato": candidato, "shortlist": shortlist})

    if pendientes_reconciliacion:
        contents_reconciliacion = json.dumps({
            "candidatos": [
                {
                    "nombre_candidato": p["candidato"].nombre,
                    "candidatos_catalogo": [
                        {"id": r["_document_id"], "nombre": r.get("nombre", ""), "tipo": r.get("tipo", "")}
                        for r in p["shortlist"]
                    ],
                }
                for p in pendientes_reconciliacion
            ],
        }, ensure_ascii=False)
        reconciliacion = gemini_client.generar_json(
            system_instruction=_PROMPT_RECONCILIACION,
            contents=contents_reconciliacion,
            response_schema=ReconciliacionRequisitos,
        )
        resueltos_por_gemini = {r.nombre_candidato: r.requisito_existente_id for r in reconciliacion.resultados}

        for p in pendientes_reconciliacion:
            candidato = p["candidato"]
            clave = p["clave"]
            ids_shortlist = {r["_document_id"] for r in p["shortlist"]}
            req_id_resuelto = resueltos_por_gemini.get(candidato.nombre)

            if req_id_resuelto and req_id_resuelto in ids_shortlist:
                resueltos_esta_pasada[clave] = req_id_resuelto
                _agregar(req_id_resuelto)
            else:
                req_id = _crear_requisito(candidato)
                nuevos_requisitos.add(req_id)
                resueltos_esta_pasada[clave] = req_id
                _agregar(req_id)

    actualizar("puestos", puesto_id, {"requisitos_extraidos": requisitos_encontrados})
    return requisitos_encontrados, nuevos_requisitos
