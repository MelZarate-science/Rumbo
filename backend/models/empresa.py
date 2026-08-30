"""Modelo de la colección `empresas`. Ver `rumbo-schema-bd.md`."""
import re
from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Empresa(BaseModel):
    empresa_id: str | None = None
    nombre_empresa: str = Field(min_length=1, max_length=120)
    contexto: str = Field(min_length=1, max_length=4000)
    email_registro: str
    password_hash: str | None = None  # nunca se serializa hacia afuera (ver routes/empresas.py)
    created_at: datetime | None = None
    activa: bool = True

    #: Nunca se serializa hacia ningún consumidor de la API.
    CAMPOS_INTERNOS: ClassVar[frozenset[str]] = frozenset({"password_hash"})


class EmpresaCreate(BaseModel):
    """Schema de entrada para crear empresa."""
    nombre_empresa: str = Field(min_length=1, max_length=120)
    contexto: str = Field(min_length=1, max_length=4000)
    email_registro: str
    password: str = Field(min_length=8, max_length=256)

    @field_validator("email_registro")
    @classmethod
    def _email_valido(cls, v: str) -> str:
        v = v.strip()
        if not _EMAIL_RE.match(v):
            raise ValueError("email inválido")
        return v.lower()

class EmpresaUpdate(BaseModel):
    """Modelo para actualización parcial de empresa."""
    nombre_empresa: str | None = Field(default=None, min_length=1, max_length=120)
    contexto: str | None = Field(default=None, min_length=1, max_length=4000)
    email_registro: str | None = None
    activa: bool | None = None

    @field_validator("email_registro")
    @classmethod
    def _email_valido(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not _EMAIL_RE.match(v):
            raise ValueError("email inválido")
        return v.lower()
