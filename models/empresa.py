"""Modelo de la colección `empresas`. Ver `rumbo-schema-bd.md`."""
from pydantic import BaseModel, Field
from datetime import datetime


class Empresa(BaseModel):
    empresa_id: str | None = None
    nombre_empresa: str
    contexto: str
    email_registro: str
    created_at: datetime | None = None
    activa: bool = True


class EmpresaCreate(BaseModel):
    """Schema de entrada para crear empresa."""
    nombre_empresa: str
    contexto: str
    email_registro: str


class EmpresaUpdate(BaseModel):
    """Modelo para actualización parcial de empresa."""
    nombre_empresa: str | None = None
    contexto: str | None = None
    email_registro: str | None = None
    activa: bool | None = None
