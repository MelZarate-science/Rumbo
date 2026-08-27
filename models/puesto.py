"""Modelo de la colección `puestos`. Ver `rumbo-schema-bd.md`."""
from pydantic import BaseModel
from datetime import datetime


class Puesto(BaseModel):
    puesto_id: str | None = None
    empresa_id: str
    titulo: str
    descripcion: str
    rol_normalizado_id: str | None = None      # lo asigna el Agente 1
    requisitos_extraidos: list[str] = []       # IDs, los asigna el Agente 2
    created_at: datetime | None = None
    activo: bool = True
