"""Modelo de la colección `roles_normalizados`. Ver `rumbo-schema-bd.md`."""
from pydantic import BaseModel
from datetime import datetime


class RequisitoFrecuencia(BaseModel):
    requisito_id: str
    cantidad: int
    porcentaje: int


class RolNormalizado(BaseModel):
    rol_normalizado_id: str | None = None      # mismo nombre que el campo que lo referencia en `puestos`
    nombre_normalizado: str
    descripcion_consolidada: str
    requisitos_frecuencia: list[RequisitoFrecuencia] = []
    requisitos_ids: list[str] = []             # copia plana, para queries array-contains
    embedding: list[float] | None = None       # contra este campo corre find_nearest()
    cantidad_puestos: int = 0
    updated_at: datetime | None = None
