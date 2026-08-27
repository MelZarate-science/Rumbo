"""Modelo de la colección `empresas`. Ver `rumbo-schema-bd.md`."""
from pydantic import BaseModel
from datetime import datetime


class Empresa(BaseModel):
    empresa_id: str | None = None
    nombre_empresa: str
    contexto: str          # el "system prompt" de la empresa: cultura, ambiente, a quién busca
    email_registro: str    # sin validación de dominio en el MVP (decisión de scope)
    created_at: datetime | None = None
    activa: bool = True
