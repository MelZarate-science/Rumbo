"""
Helpers de la capa de normalización (roles y requisitos): lectura/escritura
de la tabla de frecuencias. La parte que requiere criterio semántico vive en
los agentes 1 y 2 (Gemini), no acá.

Backlog: tareas 2.3, 2.5, 2.6
"""

from services.firestore_client import actualizar, obtener


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
