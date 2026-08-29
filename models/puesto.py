"""Modelo de la colección `puestos`. Ver `rumbo-schema-bd.md`."""
from pydantic import BaseModel, Field
from datetime import datetime


class Puesto(BaseModel):
    puesto_id: str | None = None
    empresa_id: str | None = None
    titulo: str
    descripcion: str
    rol_normalizado_id: str | None = None      # lo asigna el Agente 1
    requisitos_extraidos: list[str] = Field(default_factory=list)  # IDs, los asigna el Agente 2
    created_at: datetime | None = None
    activo: bool = True


class PuestoUpdate(BaseModel):
    """Modelo para actualización parcial de puesto (PUT)."""
    titulo: str | None = None
    descripcion: str | None = None
    activo: bool | None = None


class PuestoCreate(BaseModel):
    """Schema de entrada para crear puesto."""
    titulo: str
    descripcion: str
