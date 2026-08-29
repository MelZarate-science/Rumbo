"""
Agente 3 — Auditor de fit (MVP determinista).

Compara el `cv_data` de un perfil contra la descripción de un puesto y contra
`requisitos_frecuencia` del rol, y devuelve el score más el roadmap cuantitativo.

Corre una vez por cada puesto candidato que devolvió el retrieval.

Backlog: tareas 2.9 y 2.6
"""

from services.firestore_client import obtener
from services.normalizacion import normalizar_texto, obtener_frecuencias, texto_contiene


def _cv_texto(perfil: dict) -> str:
    """Construye un texto plano consolidado a partir del cv_data estructurado."""
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


def calcular_score_y_roadmap(perfil_id: str, puesto_id: str) -> dict:
    """
    Audita el fit entre un perfil y un puesto.

    Returns:
        {
            "score": int,               # 0-100
            "justificacion": str,
            "roadmap": [
                {
                    "requisito_id": str,
                    "nombre": str,
                    "cumplido": bool,
                    "porcentaje_mercado": int,
                    "especifico_de_esta_empresa": bool,
                    "sugerencia": str | None,
                },
                ...
            ],
        }
    """
    perfil = obtener("perfiles", perfil_id)
    puesto = obtener("puestos", puesto_id)
    if not perfil or not puesto:
        raise ValueError("perfil o puesto no encontrado")

    cv_text = _cv_texto(perfil)
    cv_norm = normalizar_texto(cv_text)

    # Requisitos del puesto
    req_ids = puesto.get("requisitos_extraidos") or []
    requisitos = []
    for req_id in req_ids:
        req = obtener("requisitos_normalizados", req_id)
        if req:
            requisitos.append(req)

    # Frecuencias del rol
    rol_id = puesto.get("rol_normalizado_id")
    freqs = {f["requisito_id"]: f for f in obtener_frecuencias(rol_id)} if rol_id else {}

    # Requisitos creados específicamente para este puesto (no en catálogo previo)
    requisitos_nuevos = set(puesto.get("requisitos_nuevos") or [])

    roadmap = []
    cumplidos = 0
    for req in requisitos:
        req_id = req["_document_id"]
        nombre = req.get("nombre", "")
        cumplido = texto_contiene(cv_text, nombre)
        if cumplido:
            cumplidos += 1

        f = freqs.get(req_id, {})
        pct_mercado = f.get("porcentaje", 0)
        # Específico si fue creado nuevo para este puesto
        especifico = req_id in requisitos_nuevos
        sugerencia = None if cumplido else f"Sumar '{nombre}' a tu perfil o experiencia."

        roadmap.append({
            "requisito_id": req_id,
            "nombre": nombre,
            "cumplido": cumplido,
            "porcentaje_mercado": pct_mercado,
            "especifico_de_esta_empresa": especifico,
            "sugerencia": sugerencia,
        })

    total = len(requisitos)
    score = round(100 * cumplidos / total) if total else 0

    if total == 0:
        justificacion = "El puesto no tiene requisitos extraídos; no se puede auditar."
    elif score >= 75:
        justificacion = f"Fuerte coincidencia: {cumplidos}/{total} requisitos cubiertos."
    elif score >= 50:
        justificacion = f"Coincidencia parcial: {cumplidos}/{total} requisitos cubiertos."
    else:
        justificacion = f"Baja coincidencia: solo {cumplidos}/{total} requisitos cubiertos."

    return {
        "score": score,
        "justificacion": justificacion,
        "roadmap": roadmap,
    }