"""
Helpers de la capa de normalización (roles y requisitos): lectura/escritura
de la tabla de frecuencias. La parte que requiere criterio semántico vive en
los agentes 1 y 2 (Gemini), no acá.

Backlog: tareas 2.3, 2.5, 2.6
"""

from backend.services.firestore_client import actualizar_transaccional


def actualizar_frecuencias(
    rol_normalizado_id: str,
    puesto_id: str,
    requisitos_ids_nuevos: list[str],
    requisitos_ids_viejos: list[str] | None = None,
) -> None:
    """
    Actualiza la tabla de frecuencias del rol.

    - `puesto_id`: el puesto que se está (re)indexando. `cantidad_puestos` se
      cuenta a partir del set real de puestos que aportaron al rol (`puestos_ids`),
      no se infiere de cuántos requisitos subieron o bajaron -- reindexar el
      mismo puesto dos veces no debe mover el contador (bug real encontrado:
      antes, editar un puesto para que pida MENOS requisitos que antes restaba
      1 de `cantidad_puestos`, como si un puesto se hubiera ido del rol).
    - `requisitos_ids_nuevos`: requisitos del puesto indexado (o re-indexado).
    - `requisitos_ids_viejos`: requisitos previos del puesto (si es reindexado).
      Se decrementan sus contadores.

    Lectura+escritura corren en una transacción de Firestore (`actualizar_transaccional`):
    dos puestos del mismo rol indexándose casi al mismo tiempo no se pisan.
    """

    def _mutar(rol: dict) -> dict:
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

        puestos_ids = set(rol.get("puestos_ids") or [])
        puestos_ids.add(puesto_id)
        cantidad_puestos = len(puestos_ids)

        for entrada in frecuencias.values():
            entrada["porcentaje"] = round(100 * entrada["cantidad"] / cantidad_puestos)

        return {
            "requisitos_frecuencia": list(frecuencias.values()),
            "requisitos_ids": list(frecuencias.keys()),
            "puestos_ids": list(puestos_ids),
            "cantidad_puestos": cantidad_puestos,
        }

    actualizar_transaccional("roles_normalizados", rol_normalizado_id, _mutar)
