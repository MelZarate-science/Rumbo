"""
Helpers de la capa de normalización (roles y requisitos).

La parte que requiere criterio semántico vive en los agentes 1 y 2;
acá están las operaciones de lectura/escritura sobre esas colecciones.

Backlog: tareas 2.3, 2.5, 2.6
"""


def actualizar_frecuencias(rol_normalizado_id: str, requisitos_ids: list[str]) -> None:
    """Incrementa conteos y recalcula porcentajes en `requisitos_frecuencia`."""
    raise NotImplementedError


def obtener_frecuencias(rol_normalizado_id: str) -> list[dict]:
    """Devuelve la tabla de frecuencias del rol, para que el Auditor la use."""
    raise NotImplementedError
