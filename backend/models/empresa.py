"""Modelo de la colección `empresas`. Ver `rumbo-schema-bd.md`."""
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class Empresa(BaseModel):
    empresa_id: str | None = None
    nombre_empresa: str
    contexto: str
    email_registro: str
    password_hash: str | None = None  # nunca se serializa hacia afuera (ver routes/empresas.py)
    created_at: datetime | None = None
    activa: bool = True

    #: Nunca se serializa hacia ningún consumidor de la API.
    CAMPOS_INTERNOS: ClassVar[frozenset[str]] = frozenset({"password_hash"})


class EmpresaCreate(BaseModel):
    """Schema de entrada para crear empresa."""
    nombre_empresa: str
    contexto: str
    email_registro: str
    password: str

    @field_validator("password")
    @classmethod
    def _password_valida(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("la contraseña debe tener al menos 8 caracteres")
        return v


class EmpresaUpdate(BaseModel):
    """Modelo para actualización parcial de empresa."""
    nombre_empresa: str | None = None
    contexto: str | None = None
    email_registro: str | None = None
    activa: bool | None = None
