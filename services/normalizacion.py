"""
Helpers de la capa de normalización (roles y requisitos).

La parte que requiere criterio semántico vive en los agentes 1 y 2;
acá están las operaciones de lectura/escritura sobre esas colecciones
más utilidades de texto compartidas por los agentes del MVP.

Backlog: tareas 2.3, 2.5, 2.6
"""

import re
import unicodedata

from services.firestore_client import actualizar, obtener


def normalizar_texto(texto: str) -> str:
    """Minúsculas, sin tildes ni signos. Unidad común de comparación del MVP."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFKD", texto.lower())
        if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", sin_tildes)).strip()


_STOPWORDS = frozenset({
    "de", "la", "el", "en", "y", "o", "a", "con", "por", "para", "un", "una",
    "los", "las", "the", "of", "to", "and", "for", "with", "in", "on",
    "buscamos", "requeridos", "experiencia", "anos", "anos", "anos", "mas",
    "se", "busca", "ofrecemos", "valorable", "imprescindible", "nivel",
    "backend", "frontend", "fullstack", "developer", "engineer", "senior",
    "junior", "lead", "tech", "stack", "anos", "ano",
    "apis", "api", "rest", "docker", "kubernetes", "k8s", "aws", "gcp", "azure",
    "cloud", "ci", "cd", "git", "github", "gitlab", "linux", "sql", "nosql",
    "microservicios", "microservice", "monolito", "arquitectura", "patrones",
    "testing", "test", "tests", "tdd", "bdd", "unit", "integration",
})


def tokens(texto: str) -> list[str]:
    """Tokens de `normalizar_texto`, sin stopwords, conservando el orden."""
    return [t for t in normalizar_texto(texto).split() if t not in _STOPWORDS]


def texto_contiene(haystack: str, needle: str) -> bool:
    """
    ¿El `needle` (nombre de un requisito/rol) entero aparece en `haystack`?
    Comparación token a token, insensible a tildes y a signos: los tokens del
    needle deben ser subconjunto de los tokens del haystack.
    """
    aguja = tokens(needle)
    if not aguja:
        return False
    pajar = set(tokens(haystack))
    return all(t in pajar for t in aguja)


def actualizar_frecuencias(
    rol_normalizado_id: str,
    requisitos_ids_nuevos: list[str],
    requisitos_ids_viejos: list[str] | None = None,
) -> None:
    """
    Actualiza la tabla de frecuencias del rol.

    - `requisitos_ids_nuevos`: requisitos del puesto indexado (o re-indexado).
    - `requisitos_ids_viejos`: requisitos previos del puesto (si es reindexado).
      Se decrementan sus contadores y se recalcula `cantidad_puestos`.
    """
    rol = obtener("roles_normalizados", rol_normalizado_id)
    if rol is None:
        return

    frecuencias = {f["requisito_id"]: f for f in rol.get("requisitos_frecuencia", [])}

    # Decrementar requisitos viejos (reindexado)
    if requisitos_ids_viejos:
        for req_id in requisitos_ids_viejos:
            entrada = frecuencias.get(req_id)
            if entrada:
                entrada["cantidad"] = max(0, entrada["cantidad"] - 1)
                if entrada["cantidad"] == 0:
                    del frecuencias[req_id]

    # Incrementar requisitos nuevos
    for req_id in requisitos_ids_nuevos:
        entrada = frecuencias.get(req_id)
        if entrada is None:
            frecuencias[req_id] = {"requisito_id": req_id, "cantidad": 1, "porcentaje": 0}
        else:
            entrada["cantidad"] += 1

    # Recalcular cantidad_puestos: suma de todos los contadores / 1 puesto = promedio
    # Pero más simple: cantidad_puestos = total requisitos únicos en el rol
    # (aproximación MVP: cada puesto suma 1 al total)
    cantidad_actual = rol.get("cantidad_puestos") or 0
    delta = len(requisitos_ids_nuevos) - len(requisitos_ids_viejos or [])
    cantidad_puestos = max(1, cantidad_actual + (1 if delta >= 0 else -1))

    for entrada in frecuencias.values():
        entrada["porcentaje"] = round(100 * entrada["cantidad"] / cantidad_puestos)

    ids_planos = list(frecuencias.keys())
    actualizar("roles_normalizados", rol_normalizado_id, {
        "requisitos_frecuencia": list(frecuencias.values()),
        "requisitos_ids": ids_planos,
        "cantidad_puestos": cantidad_puestos,
    })


def obtener_frecuencias(rol_normalizado_id: str) -> list[dict]:
    """Devuelve la tabla de frecuencias del rol, para que el Auditor la use."""
    rol = obtener("roles_normalizados", rol_normalizado_id)
    if rol is None:
        return []
    return rol.get("requisitos_frecuencia", [])
