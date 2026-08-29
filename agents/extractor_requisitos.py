"""
Agente 2 — Extractor de requisitos (MVP determinista).

Descompone la descripción en texto libre de un puesto en requisitos discretos,
reconciliándolos contra `requisitos_normalizados` (reconoce que "manejo de
bases de datos" y "SQL" son la misma entidad vía coincidencia de tokens).

Backlog: tareas 2.5 y 2.6
"""

from services.firestore_client import crear, listar, obtener
from services.normalizacion import actualizar_frecuencias, normalizar_texto, texto_contiene, tokens as norm_tokens


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
    texto_norm = normalizar_texto(texto)

    # 1) Catálogo existente: buscamos cuáles de los requisitos normalizados
    #    aparecen (por tokens) en el texto del puesto
    catalogo = listar("requisitos_normalizados")
    requisitos_encontrados = []
    for req in catalogo:
        nombre = req.get("nombre", "")
        if texto_contiene(texto, nombre):
            requisitos_encontrados.append(req["_document_id"])

    # 2) Fallback MVP: si no hubo coincidencias, crear requisitos a partir
    #    de tokens "habilidad" del texto (palabras >= 3 chars, no stopwords)
    nuevos_requisitos = set()
    if not requisitos_encontrados:
        tokens_texto = norm_tokens(texto)
        # Tomamos hasta 8 tokens únicos como requisitos
        vistos = set()
        for t in tokens_texto:
            if t in vistos:
                continue
            vistos.add(t)
            req_id = crear("requisitos_normalizados", {
                "nombre": t.capitalize(),
                "tipo": "herramienta",
            })
            requisitos_encontrados.append(req_id)
            nuevos_requisitos.add(req_id)
            if len(requisitos_encontrados) >= 8:
                break

    # 3) Guardar en el puesto
    from services.firestore_client import actualizar
    actualizar("puestos", puesto_id, {"requisitos_extraidos": requisitos_encontrados})

    # 4) Actualizar frecuencias del rol
    rol_id = puesto.get("rol_normalizado_id")
    if rol_id:
        actualizar_frecuencias(rol_id, requisitos_encontrados)

    return requisitos_encontrados, nuevos_requisitos