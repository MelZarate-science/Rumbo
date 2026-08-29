"""
Fake determinista de Gemini para tests — sin red ni credenciales.

Reimplementa, a propósito, una heurística de solapamiento de texto como
sustituto del razonamiento real del modelo. No es "inteligente" — es un doble
de prueba que permite verificar que el código arma el payload correcto, llama
al modelo, y usa la respuesta como se espera, sin depender de si Gemini está
disponible. La calidad semántica real solo se puede validar contra la API
de verdad (ver README, sección de credenciales).
"""

import hashlib
import json
import re
import unicodedata

_DIM_EMBEDDING = 64


def _normalizar(texto: str) -> str:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFKD", (texto or "").lower())
        if not unicodedata.combining(c)
    )
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes).strip()


def _tokens(texto: str) -> set[str]:
    return {t for t in _normalizar(texto).split() if len(t) > 2}


def fake_generar_json(*, system_instruction, contents, response_schema, model=None, temperature=0.0):
    payload = json.loads(contents)
    nombre_schema = response_schema.__name__

    if nombre_schema == "ClasificacionRol":
        return _fake_clasificacion(payload, response_schema)
    if nombre_schema == "ExtraccionRequisitos":
        return _fake_extraccion(payload, response_schema)
    if nombre_schema == "AuditoriaFit":
        return _fake_auditoria(payload, response_schema)
    raise NotImplementedError(f"FakeGemini no soporta el esquema {nombre_schema}")


def _fake_clasificacion(payload, schema):
    puesto = payload["puesto"]
    puesto_tokens = _tokens(f"{puesto['titulo']} {puesto['descripcion']}")

    mejor, mejor_score = None, 0
    for rol in payload["catalogo_roles"]:
        rol_tokens = _tokens(f"{rol['nombre_normalizado']} {rol['descripcion_consolidada']}")
        solapamiento = len(puesto_tokens & rol_tokens)
        if solapamiento > mejor_score:
            mejor_score, mejor = solapamiento, rol

    if mejor and mejor_score > 0:
        return schema(
            es_rol_nuevo=False,
            rol_existente_id=mejor["id"],
            nombre_normalizado=mejor["nombre_normalizado"],
            descripcion_consolidada=mejor["descripcion_consolidada"],
        )
    return schema(
        es_rol_nuevo=True,
        rol_existente_id=None,
        nombre_normalizado=puesto["titulo"],
        descripcion_consolidada=puesto["descripcion"],
    )


def _fake_extraccion(payload, schema):
    puesto = payload["puesto"]
    texto_puesto = f"{puesto['titulo']} {puesto['descripcion']}"
    tokens_puesto = _tokens(texto_puesto)

    from agents.extractor_requisitos import RequisitoDetectado

    detectados = []
    tokens_cubiertos: set[str] = set()

    for req in payload["catalogo_requisitos"]:
        tokens_req = _tokens(req["nombre"])
        if tokens_req and tokens_req.issubset(tokens_puesto):
            detectados.append(RequisitoDetectado(
                requisito_existente_id=req["id"], nombre=req["nombre"], tipo=req.get("tipo"),
            ))
            tokens_cubiertos |= tokens_req

    restantes = sorted(tokens_puesto - tokens_cubiertos)
    for tok in restantes[:8]:
        detectados.append(RequisitoDetectado(
            requisito_existente_id=None, nombre=tok.capitalize(), tipo="herramienta",
        ))

    return schema(requisitos=detectados)


def _fake_auditoria(payload, schema):
    from agents.auditor_fit import EvaluacionRequisito

    tokens_cv = _tokens(payload.get("cv_texto", ""))
    requisitos = payload["requisitos"]

    evaluaciones = []
    cumplidos = 0
    for req in requisitos:
        tokens_req = _tokens(req["nombre"])
        cumplido = bool(tokens_req) and tokens_req.issubset(tokens_cv)
        if cumplido:
            cumplidos += 1
        evaluaciones.append(EvaluacionRequisito(
            requisito_id=req["id"],
            cumplido=cumplido,
            sugerencia=None if cumplido else f"Sumar '{req['nombre']}' a tu perfil o experiencia.",
        ))

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

    return schema(score=score, justificacion=justificacion, evaluaciones=evaluaciones)


def fake_generar_embedding_vector(texto: str, *, model: str | None = None) -> list[float]:
    """
    Vector determinista por hashing de tokens (bag-of-words), NO un embedding
    semántico real. Alcanza para que `find_nearest()` en el fake de Firestore
    ordene por solapamiento de vocabulario en los tests.
    """
    if not texto or not texto.strip():
        return []

    vector = [0.0] * _DIM_EMBEDDING
    for tok in _tokens(texto):
        idx = int(hashlib.sha256(tok.encode("utf-8")).hexdigest(), 16) % _DIM_EMBEDDING
        vector[idx] += 1.0

    norma = sum(v * v for v in vector) ** 0.5
    if norma == 0:
        return vector
    return [v / norma for v in vector]
