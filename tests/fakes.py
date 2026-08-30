"""
Fake in-memory Firestore para tests — sin dependencia de emulador ni GCP.

Simula la API mínima que usa `services.firestore_client`:
- collection(name) -> FakeCollection
- document(id) -> FakeDocumentRef
- get() -> FakeDocumentSnapshot (exists, to_dict(), id)
- set(data), update(data)
- stream() -> iterable de FakeDocumentSnapshot
- where(field, op, value) chaining
"""

import math
from copy import deepcopy
from typing import Any


def _desenvolver_vectores(data: dict) -> dict:
    """Convierte `Vector` de Firestore a `list[float]` plana para el fake."""
    from google.cloud.firestore_v1.vector import Vector

    return {k: (list(v) if isinstance(v, Vector) else v) for k, v in data.items()}


def _coseno(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return -1.0
    dot = sum(x * y for x, y in zip(a, b))
    norma_a = math.sqrt(sum(x * x for x in a))
    norma_b = math.sqrt(sum(y * y for y in b))
    if norma_a == 0 or norma_b == 0:
        return -1.0
    return dot / (norma_a * norma_b)


class _FakeVectorQuery:
    """Simula `find_nearest()`: ordena por similitud coseno, sin índice real."""

    def __init__(
        self, collection: "FakeCollection", vector_field: str, query_vector, limit: int,
        distance_threshold: float | None = None,
    ):
        self._collection = collection
        self._vector_field = vector_field
        self._query_vector = list(query_vector)
        self._limit = limit
        self._distance_threshold = distance_threshold

    def stream(self):
        candidatos = []
        for doc in self._collection._docs.values():
            valor = doc["data"].get(self._vector_field)
            if not valor:
                continue
            similitud = _coseno(list(valor), self._query_vector)
            distancia = 1 - similitud  # aproximación de distancia coseno, alcanza para el fake
            if self._distance_threshold is not None and distancia > self._distance_threshold:
                continue
            candidatos.append((similitud, doc))
        candidatos.sort(key=lambda c: c[0], reverse=True)
        for _, doc in candidatos[: self._limit]:
            yield FakeDocumentSnapshot(doc["_id"], doc["data"])


class _FakeQuery:
    def __init__(self, collection: "FakeCollection", filters: list[tuple] | None = None):
        self._collection = collection
        self._filters = filters or []

    def where(self, field: str, op: str, value: Any):
        if op not in ("==", "in"):
            raise NotImplementedError(f"FakeQuery solo soporta == e in, no {op}")
        new_filters = self._filters + [(field, op, value)]
        return _FakeQuery(self._collection, new_filters)

    def stream(self):
        for doc in self._collection._docs.values():
            if self._match(doc):
                yield FakeDocumentSnapshot(doc["_id"], doc["data"])

    def _match(self, doc: dict) -> bool:
        data = doc["data"]
        for field, op, value in self._filters:
            if field not in data:
                return False
            if op == "==":
                if data[field] != value:
                    return False
            elif op == "in":
                if data[field] not in value:
                    return False
        return True


class FakeDocumentSnapshot:
    def __init__(self, doc_id: str, data: dict):
        self.id = doc_id
        self._data = data
        self.exists = True

    def to_dict(self) -> dict:
        return deepcopy(self._data)


class FakeDocumentRef:
    def __init__(self, collection: "FakeCollection", doc_id: str | None = None):
        self._collection = collection
        self._id = doc_id

    @property
    def id(self) -> str:
        return self._id

    def get(self, transaction=None) -> FakeDocumentSnapshot:
        if self._id is None or self._id not in self._collection._docs:
            snap = FakeDocumentSnapshot("", {})
            snap.exists = False
            return snap
        doc = self._collection._docs[self._id]
        return FakeDocumentSnapshot(doc["_id"], doc["data"])

    def set(self, data: dict) -> None:
        if self._id is None:
            raise ValueError("DocumentRef sin ID no puede hacer set")
        self._collection._docs[self._id] = {"_id": self._id, "data": deepcopy(_desenvolver_vectores(data))}

    def update(self, data: dict) -> None:
        if self._id is None or self._id not in self._collection._docs:
            raise KeyError(f"Documento {self._id} no existe para update")
        self._collection._docs[self._id]["data"].update(deepcopy(_desenvolver_vectores(data)))


class FakeCollection:
    def __init__(self, name: str, db: "FakeFirestore"):
        self.name = name
        self._db = db
        self._docs: dict[str, dict] = {}

    def document(self, doc_id: str | None = None) -> FakeDocumentRef:
        if doc_id is None:
            # Generar ID aleatorio simple
            import uuid
            doc_id = uuid.uuid4().hex[:20]
        return FakeDocumentRef(self, doc_id)

    def where(self, field: str, op: str, value: Any) -> _FakeQuery:
        return _FakeQuery(self).where(field, op, value)

    def find_nearest(
        self, vector_field: str, query_vector, limit: int, distance_measure=None,
        distance_threshold: float | None = None, **kwargs,
    ) -> _FakeVectorQuery:
        return _FakeVectorQuery(self, vector_field, query_vector, limit, distance_threshold)

    def stream(self):
        for doc in self._docs.values():
            yield FakeDocumentSnapshot(doc["_id"], doc["data"])

    def clear(self):
        self._docs.clear()


class FakeTransaction:
    """
    Fake mínimo de `Transaction`: el decorador real `firestore.transactional`
    (se importa el módulo real del SDK, no un doble) maneja su propio ciclo
    de vida contra este objeto -- alcanza con exponer los métodos que llama
    (`_clean_up`, `_begin`, `_commit`, `_rollback`) y los atributos que lee
    (`_max_attempts`, `_read_only`). No hay concurrencia real que resolver en
    el fake (un solo proceso, en memoria): las escrituras de `update()` se
    aplican directo, sin buffer ni conflicto posible dentro de un test.
    """
    _max_attempts = 5
    _read_only = False

    def __init__(self):
        self._id = None

    def _clean_up(self):
        pass

    def _begin(self, retry_id=None):
        self._id = retry_id or "fake-tx"

    def _commit(self):
        pass

    def _rollback(self):
        pass

    def update(self, ref: FakeDocumentRef, data: dict) -> None:
        ref.update(data)


class FakeFirestore:
    """Cliente fake compatible con la API usada en firestore_client."""
    def __init__(self):
        self._collections: dict[str, FakeCollection] = {}

    def collection(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection(name, self)
        return self._collections[name]

    def transaction(self) -> FakeTransaction:
        return FakeTransaction()

    def clear_all(self):
        for coll in self._collections.values():
            coll.clear()


# Instancia global para el fixture de test
FAKE_DB = FakeFirestore()