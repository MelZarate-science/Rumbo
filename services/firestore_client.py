"""
Único punto de acceso a Firestore.

REGLA DEL EQUIPO: nadie llama a Firestore directamente desde un endpoint,
un agente o el pipeline. Todo pasa por acá, para que no existan cuatro
formas distintas de leer/escribir la misma colección.

Ver `rumbo-contrato-interfaces.md`, sección 4.

Convenciones (las cumplen todos los consumidores):
- El ID del documento lo genera Firestore en `crear`, que devuelve ese ID.
- `obtener` y `listar` devuelven dicts con los campos del documento más la
  clave `_document_id`, que el llamador mapea al campo `<entidad>_id` del
  modelo Pydantic correspondiente.
- Las fechas se guardan como `datetime` (Firestore las almacena como
  timestamps y las devuelve como `datetime`).
- Toda falla de acceso se envuelve en `FirestoreError`; los endpoints la
  convierten en la respuesta de error estándar del contrato.

Para correr local sin credenciales de GCP: `export FIRESTORE_EMULATOR_HOST=localhost:8080`
y levantar el emulador (`gcloud emulators firestore start`).
"""

import logging
import os

log = logging.getLogger(__name__)

_CLIENT = None


class FirestoreError(RuntimeError):
    """Error de acceso a Firestore. El mensaje es siempre apto para log, no para el frontend."""


def _client():
    """
    Devuelve el cliente de Firestore, creándolo en el primer uso.

    Lazy a propósito: importar el módulo no toca GCP. Las variables
    respetadas son GOOGLE_CLOUD_PROJECT y FIRESTORE_DATABASE_ID; con
    FIRESTORE_EMULATOR_HOST seteada, el SDK va contra el emulador.
    """
    global _CLIENT
    if _CLIENT is None:
        from google.cloud import firestore

        project = os.getenv("GOOGLE_CLOUD_PROJECT") or None
        database = os.getenv("FIRESTORE_DATABASE_ID") or "(default)"
        _CLIENT = firestore.Client(project=project, database=database)
        log.info("Firestore conectado (project=%r, database=%r)", _CLIENT.project, database)
    return _CLIENT


def obtener(coleccion: str, doc_id: str) -> dict | None:
    """
    Devuelve el documento como dict, con `_document_id` incluido,
    o None si no existe.
    """
    try:
        doc = _client().collection(coleccion).document(doc_id).get()
    except Exception as exc:  # noqa: BLE001 — re-empacado uniforme
        raise FirestoreError(f"obtener {coleccion}/{doc_id}: {exc}") from exc
    if not doc.exists:
        return None
    return {**doc.to_dict(), "_document_id": doc.id}


def crear(coleccion: str, datos: dict) -> str:
    """
    Crea el documento con un ID generado por Firestore.

    Returns: el ID del documento creado.
    """
    try:
        ref = _client().collection(coleccion).document()
        ref.set(datos)
    except Exception as exc:  # noqa: BLE001
        raise FirestoreError(f"crear en {coleccion}: {exc}") from exc
    return ref.id


def actualizar(coleccion: str, doc_id: str, datos: dict) -> None:
    """
    Actualiza campos del documento (merge). None si no existía.
    """
    try:
        _client().collection(coleccion).document(doc_id).update(datos)
    except Exception as exc:  # noqa: BLE001
        raise FirestoreError(f"actualizar {coleccion}/{doc_id}: {exc}") from exc


def listar(coleccion: str, filtros: dict | None = None) -> list[dict]:
    """
    Lista documentos. `filtros` es un dict campo -> valor, aplicado como
    igualdades encadenadas. Si un valor es una lista/tupla/set, se interpreta
    como filtro `in` (Firestore admite hasta 30 valores por cláusula).

    Cada dict devuelto incluye `_document_id`.
    """
    try:
        query = _client().collection(coleccion)
        if filtros:
            for campo, valor in filtros.items():
                if isinstance(valor, (list, tuple, set)):
                    query = query.where(campo, "in", list(valor))
                else:
                    query = query.where(campo, "==", valor)
        docs = query.stream()
        return [{**doc.to_dict(), "_document_id": doc.id} for doc in docs]
    except Exception as exc:  # noqa: BLE001
        raise FirestoreError(f"listar {coleccion}: {exc}") from exc
