"""
Agente 3 — Auditor de fit.

Compara el `cv_data` de un perfil contra la descripción de un puesto y contra
`requisitos_frecuencia` del rol, con razonamiento semántico real (Gemini), y
devuelve el score más el roadmap cuantitativo. Ver
`agents/prompts/auditor_fit_prompt.txt`.

Lo que decide el modelo: si el CV cumple cada requisito (evidencia semántica,
no solo coincidencia de palabra), el score global y la sugerencia para cada
requisito no cumplido. Lo que NO decide el modelo (son datos objetivos que ya
tenemos): `porcentaje_mercado` (viene de `requisitos_frecuencia` del rol) y
`especifico_de_esta_empresa` (si el requisito se creó recién para este puesto).

Corre una vez por cada puesto candidato que devolvió el retrieval.

Backlog: tareas 2.9 y 2.6
"""

import json
from pathlib import Path

from pydantic import BaseModel

from services import gemini_client
from services.firestore_client import obtener
from services.normalizacion import obtener_frecuencias

_PROMPT = (Path(__file__).parent / "prompts" / "auditor_fit_prompt.txt").read_text(encoding="utf-8")


class EvaluacionRequisito(BaseModel):
    requisito_id: str
    cumplido: bool
    sugerencia: str | None


class AuditoriaFit(BaseModel):
    score: int
    justificacion: str
    evaluaciones: list[EvaluacionRequisito]


def _cv_texto(perfil: dict) -> str:
    """Construye un texto plano consolidado a partir del cv_data estructurado."""
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


def calcular_score_y_roadmap(perfil_id: str, puesto_id: str) -> dict:
    """
    Audita el fit entre un perfil y un puesto (Agente 3, Gemini).

    Returns:
        {"score": int, "justificacion": str, "roadmap": [RoadmapItem, ...]}
    """
    perfil = obtener("perfiles", perfil_id)
    puesto = obtener("puestos", puesto_id)
    if not perfil or not puesto:
        raise ValueError("perfil o puesto no encontrado")

    cv_text = _cv_texto(perfil)

    req_ids = puesto.get("requisitos_extraidos") or []
    requisitos = []
    for req_id in req_ids:
        req = obtener("requisitos_normalizados", req_id)
        if req:
            requisitos.append(req)

    rol_id = puesto.get("rol_normalizado_id")
    freqs = {f["requisito_id"]: f for f in obtener_frecuencias(rol_id)} if rol_id else {}
    requisitos_nuevos = set(puesto.get("requisitos_nuevos") or [])

    if not requisitos:
        return {
            "score": 0,
            "justificacion": "El puesto no tiene requisitos extraídos; no se puede auditar.",
            "roadmap": [],
        }

    contents = json.dumps({
        "cv_texto": cv_text,
        "requisitos": [
            {
                "id": req["_document_id"],
                "nombre": req.get("nombre", ""),
                "porcentaje_mercado": freqs.get(req["_document_id"], {}).get("porcentaje", 0),
                "especifico_de_esta_empresa": req["_document_id"] in requisitos_nuevos,
            }
            for req in requisitos
        ],
    }, ensure_ascii=False)

    resultado = gemini_client.generar_json(
        system_instruction=_PROMPT,
        contents=contents,
        response_schema=AuditoriaFit,
    )
    evaluaciones = {e.requisito_id: e for e in resultado.evaluaciones}

    roadmap = []
    for req in requisitos:
        req_id = req["_document_id"]
        nombre = req.get("nombre", "")
        evaluacion = evaluaciones.get(req_id)
        cumplido = evaluacion.cumplido if evaluacion else False
        sugerencia = evaluacion.sugerencia if evaluacion else f"Sumar '{nombre}' a tu perfil o experiencia."
        if cumplido:
            sugerencia = None

        f = freqs.get(req_id, {})
        roadmap.append({
            "requisito_id": req_id,
            "nombre": nombre,
            "cumplido": cumplido,
            "porcentaje_mercado": f.get("porcentaje", 0),
            "especifico_de_esta_empresa": req_id in requisitos_nuevos,
            "sugerencia": sugerencia,
        })

    score = max(0, min(100, resultado.score))

    return {
        "score": score,
        "justificacion": resultado.justificacion,
        "roadmap": roadmap,
    }
