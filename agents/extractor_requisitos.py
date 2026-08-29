"""
Agente 2 — Extractor de requisitos (MVP determinista).

Descompone la descripción en texto libre de un puesto en requisitos discretos,
reconciliándolos contra `requisitos_normalizados` (reconoce que "manejo de
bases de datos" y "SQL" son la misma entidad vía coincidencia de tokens).

Backlog: tareas 2.5 y 2.6
"""

from services.firestore_client import crear, listar, obtener
from services.normalizacion import normalizar_texto, texto_contiene, tokens as norm_tokens


def extraer_requisitos(puesto_id: str) -> tuple[list[str], set[str]]:
    """
    Extrae los requisitos del puesto y actualiza las frecuencias del rol.

    Args:
        puesto_id: ID del documento en la colección `puestos`.

    Returns:
        Tupla (lista de `requisito_id`, set de `requisito_id` creados nuevos).
    """
    puesto = obtener("puestos", puesto_id)
    if puesto is None:
        raise ValueError(f"puesto {puesto_id} no encontrado")

    texto = " ".join(filter(None, [puesto.get("titulo"), puesto.get("descripcion")]))

    # 1) Catálogo existente: buscamos cuáles de los requisitos normalizados
    #    aparecen (por tokens) en el texto del puesto
    catalogo = listar("requisitos_normalizados")
    requisitos_encontrados = []
    tokens_cubiertos = set()
    for req in catalogo:
        nombre = req.get("nombre", "")
        if texto_contiene(texto, nombre):
            requisitos_encontrados.append(req["_document_id"])
            tokens_cubiertos.update(norm_tokens(nombre))

    # 2) Siempre buscar requisitos adicionales en tokens del texto
    #    que no estén cubiertos por el catálogo existente
    nuevos_requisitos = set()
    tokens_texto = norm_tokens(texto)
    vistos = set()
    for t in tokens_texto:
        if t in vistos or t in tokens_cubiertos:
            continue
        vistos.add(t)
        req_id = crear("requisitos_normalizados", {
            "nombre": t.capitalize(),
            "tipo": "herramienta",
        })
        requisitos_encontrados.append(req_id)
        nuevos_requisitos.add(req_id)
        if len(requisitos_encontrados) >= 12:  # límite mayor para combinar catálogo + nuevos
            break

    # 3) Guardar en el puesto
    from services.firestore_client import actualizar
    actualizar("puestos", puesto_id, {"requisitos_extraidos": requisitos_encontrados})

    # 4) Actualizar frecuencias del rol (se hace en pipeline/indexado para idempotencia)
    #    No llamamos actualizar_frecuencias aquí; lo hace ejecutar_pipeline_indexado
    #    con los requisitos viejos y nuevos para idempotencia.

    return requisitos_encontrados, nuevos_requisitos