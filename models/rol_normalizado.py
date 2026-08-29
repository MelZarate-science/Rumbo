"""Modelo de la colección `roles_normalizados`. Ver `rumbo-schema-bd.md`."""
from pydantic import BaseModel, Field
from datetime import datetime


class RequisitoFrecuencia(BaseModel):
    requisito_id: str
    cantidad: int
    porcentaje: int


class RolNormalizado(BaseModel):
    rol_normalizado_id: str | None = None      # mismo nombre que el campo que lo referencia en `puestos`
    nombre_normalizado: str
    descripcion_consolidada: str
    requisitos_frecuencia: list[RequisitoFrecuencia] = Field(default_factory=list)
    requisitos_ids: list[str] = Field(default_factory=list)  # copia plana, queries array-contains
    embedding: list[float] | None = None       # diferido fuera del MVP (ver backend.md Fase 4)
    cantidad_puestos: int = 0
    updated_at: datetime | None = None
