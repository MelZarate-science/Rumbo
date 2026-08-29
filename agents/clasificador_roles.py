"""
Agente 1 — Clasificador de roles (MVP determinista).

Recibe un puesto recién cargado y decide si pertenece a un rol ya existente
en `roles_normalizados` o si hay que crear uno nuevo.

Estrategia MVP: coincidencia por solapamiento de tokens normalizados entre
el título del puesto y los `nombre_normalizado` de los roles existentes.
Si ningún rol solapa al menos 1 token, se crea uno nuevo.

Backlog: tarea 2.3
"""

from models.puesto import Puesto
from services.firestore_client import crear, listar, obtener
from services.normalizacion import normalizar_texto, tokens


def clasificar_puesto(puesto_id: str) -> str:
    """
    Asigna un `rol_normalizado_id` al puesto.

    Args:
        puesto_id: ID del documento en la colección `puestos`.

    Returns:
        El `rol_normalizado_id` asignado (existente o recién creado).
    """
    puesto = obtener("puestos", puesto_id)
    if puesto is None:
        raise ValueError(f"puesto {puesto_id} no encontrado")

    titulo = puesto.get("titulo", "")
    puesto_tokens = set(tokens(titulo))

    roles = listar("roles_normalizados")
    mejor_rol = None
    mejor_solapamiento = 0

    for rol in roles:
        nombre = rol.get("nombre_normalizado", "")
        solapamiento = len(puesto_tokens & set(tokens(nombre)))
        if solapamiento > mejor_solapamiento:
            mejor_solapamiento = solapamiento
            mejor_rol = rol

    if mejor_rol and mejor_solapamiento > 0:
        rol_id = mejor_rol["_document_id"]
    else:
        rol_id = crear("roles_normalizados", {
            "nombre_normalizado": titulo,
            "descripcion_consolidada": puesto.get("descripcion", ""),
            "requisitos_frecuencia": [],
            "requisitos_ids": [],
            "cantidad_puestos": 0,
        })

    # Actualizar el puesto con el rol asignado
    from services.firestore_client import actualizar
    actualizar("puestos", puesto_id, {"rol_normalizado_id": rol_id})

    return rol_id