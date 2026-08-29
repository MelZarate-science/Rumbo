"""
Retrieval en dos niveles. NINGUNO de los dos usa el modelo de razonamiento —
esa es justamente la decisión de arquitectura que mantiene bajo el costo.

Nivel 1: búsqueda semántica aproximada (token-overlap) contra roles_normalizados.
Nivel 2: filtro simple y gratis, contra la colección grande (puestos).

Backlog: tareas 2.7 y 2.8
"""

from services.firestore_client import listar, obtener
from services.normalizacion import normalizar_texto, tokens


def buscar_roles_afines(perfil_id: str, limite: int = 3) -> list[str]:
    """
    NIVEL 1 — matching por solapamiento de tokens entre el texto consolidado
    del perfil y los `nombre_normalizado` + `descripcion_consolidada` de los roles.

    Returns: lista de `rol_normalizado_id`, los más afines primero.
    """
    perfil = obtener("perfiles", perfil_id)
    if not perfil:
        return []

    cv_text = _cv_texto(perfil)
    perfil_tokens = set(tokens(cv_text))

    roles = listar("roles_normalizados")
    scores = []
    for rol in roles:
        rol_texto = " ".join(filter(None, [
            rol.get("nombre_normalizado", ""),
            rol.get("descripcion_consolidada", ""),
        ]))
        rol_tokens = set(tokens(rol_texto))
        solapamiento = len(perfil_tokens & rol_tokens)
        if solapamiento > 0:
            scores.append((solapamiento, rol["_document_id"]))

    scores.sort(reverse=True, key=lambda x: x[0])
    return [rid for _, rid in scores[:limite]]


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


def _cv_texto(perfil: dict) -> str:
    """Construye texto consolidado igual que el auditor."""
    partes = []
    cv = perfil.get("cv_data", {}) or {}
    if cv.get("cv_texto_original"):
        partes.append(cv["cv_texto_original"])
    for exp in cv.get("experiencia", []):
        partes.append(exp.get("descripcion", ""))
    for form in cv.get("formacion", []):
        partes.append(form.get("descripcion", "") or form.get("titulo", ""))
    partes.extend(cv.get("habilidades", []))
    for proj in cv.get("proyectos", []):
        partes.append(proj.get("descripcion", ""))
    return " ".join(filter(None, partes))