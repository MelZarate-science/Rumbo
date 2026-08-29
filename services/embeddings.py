"""
Generación de embeddings. Diferido fuera del MVP (ver `backend.md` Fase 4).

El MVP usa retrieval por solapamiento de tokens determinista (ver
`services/retrieval.py`). Esta función existe para no romper imports,
pero no se usa en el flujo crítico.
"""

import logging

log = logging.getLogger(__name__)


def generar_embedding(texto: str) -> list[float]:
    """Devuelve vector vacío; el MVP no usa embeddings."""
    log.warning("generar_embedding llamado pero deshabilitado en el MVP")
    return []


def generar_embedding_perfil(perfil_id: str) -> list[float]:
    """Consolida el cv_data del perfil en texto y genera su embedding."""
    log.warning("generar_embedding_perfil llamado pero deshabilitado en el MVP")
    return []


def generar_embedding_rol(rol_normalizado_id: str) -> list[float]:
    """Genera el embedding de la descripcion_consolidada del rol."""
    log.warning("generar_embedding_rol llamado pero deshabilitado en el MVP")
    return []