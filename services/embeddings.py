"""
Generación de embeddings. No usa razonamiento del modelo: es una llamada
directa al modelo de embeddings de Vertex AI.

Backlog: tareas 2.2 y 2.4
"""


def generar_embedding(texto: str) -> list[float]:
    """Devuelve el vector, sin importar si es para un perfil o un rol."""
    raise NotImplementedError


def generar_embedding_perfil(perfil_id: str) -> list[float]:
    """Consolida el cv_data del perfil en texto y genera su embedding."""
    raise NotImplementedError


def generar_embedding_rol(rol_normalizado_id: str) -> list[float]:
    """Genera el embedding de la descripcion_consolidada del rol."""
    raise NotImplementedError
