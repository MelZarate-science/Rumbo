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

from copy import deepcopy
from typing import Any


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

    def get(self) -> FakeDocumentSnapshot:
        if self._id is None or self._id not in self._collection._docs:
            snap = FakeDocumentSnapshot("", {})
            snap.exists = False
            return snap
        doc = self._collection._docs[self._id]
        return FakeDocumentSnapshot(doc["_id"], doc["data"])

    def set(self, data: dict) -> None:
        if self._id is None:
            raise ValueError("DocumentRef sin ID no puede hacer set")
        self._collection._docs[self._id] = {"_id": self._id, "data": deepcopy(data)}

    def update(self, data: dict) -> None:
        if self._id is None or self._id not in self._collection._docs:
            raise KeyError(f"Documento {self._id} no existe para update")
        self._collection._docs[self._id]["data"].update(deepcopy(data))


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

    def stream(self):
        for doc in self._docs.values():
            yield FakeDocumentSnapshot(doc["_id"], doc["data"])

    def clear(self):
        self._docs.clear()


class FakeFirestore:
    """Cliente fake compatible con la API usada en firestore_client."""
    def __init__(self):
        self._collections: dict[str, FakeCollection] = {}

    def collection(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection(name, self)
        return self._collections[name]

    def clear_all(self):
        for coll in self._collections.values():
            coll.clear()


# Instancia global para el fixture de test
FAKE_DB = FakeFirestore()