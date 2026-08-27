"""
Único punto de acceso a Firestore.

REGLA DEL EQUIPO: nadie llama a Firestore directamente desde un endpoint,
un agente o el pipeline. Todo pasa por acá, para que no existan cuatro
formas distintas de leer/escribir la misma colección.

Ver `rumbo-contrato-interfaces.md`, sección 4.
"""


def obtener(coleccion: str, doc_id: str) -> dict | None:
    raise NotImplementedError


def crear(coleccion: str, datos: dict) -> str:
    """Returns: el ID del documento creado."""
    raise NotImplementedError


def actualizar(coleccion: str, doc_id: str, datos: dict) -> None:
    raise NotImplementedError


def listar(coleccion: str, filtros: dict | None = None) -> list[dict]:
    raise NotImplementedError
