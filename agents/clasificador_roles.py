"""
Agente 1 — Clasificador de roles.

Recibe un puesto recién cargado y decide si pertenece a un rol ya existente
en `roles_normalizados` o si hay que crear uno nuevo.

Requiere razonamiento semántico: entender que "Líder de Producto", "PM" y
"Product Manager" son el mismo rol, pero "Product Marketing Manager" no.

Backlog: tarea 2.3
"""


def clasificar_puesto(puesto_id: str) -> str:
    """
    Asigna un `rol_normalizado_id` al puesto.

    Args:
        puesto_id: ID del documento en la colección `puestos`.

    Returns:
        El `rol_normalizado_id` asignado (existente o recién creado).
    """
    raise NotImplementedError
