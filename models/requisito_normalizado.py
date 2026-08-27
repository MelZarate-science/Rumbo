"""Modelo de la colección `requisitos_normalizados`. Ver `rumbo-schema-bd.md`."""
from pydantic import BaseModel
from datetime import datetime


class RequisitoNormalizado(BaseModel):
    requisito_id: str | None = None
    nombre: str
    tipo: str | None = None        # herramienta | habilidad_blanda | certificacion
    created_at: datetime | None = None
