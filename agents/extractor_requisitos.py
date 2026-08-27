"""
Agente 2 — Extractor de requisitos.

Descompone la descripción en texto libre de un puesto en requisitos discretos,
reconciliándolos contra `requisitos_normalizados` (reconoce que "manejo de bases
de datos" y "SQL" son la misma entidad). Después actualiza la tabla de
frecuencias del rol correspondiente.

Backlog: tareas 2.5 y 2.6
"""


def extraer_requisitos(puesto_id: str) -> list[str]:
    """
    Extrae los requisitos del puesto y actualiza las frecuencias del rol.

    Args:
        puesto_id: ID del documento en la colección `puestos`.

    Returns:
        Lista de `requisito_id` (referencias a `requisitos_normalizados`).
    """
    raise NotImplementedError
