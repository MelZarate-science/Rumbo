"""Modelo de la colección `perfiles`. Ver `rumbo-schema-bd.md`."""
import re
from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
"""Formato básico de email. No pretendemos RFC 5322 completo: sólo bloquear
errores de carga comunes en el MVP."""

_TELEFONO_RE = re.compile(r"^\+?[\d\s().-]{5,20}$")
"""Formato libre pero numérico, con opcional prefijo internacional."""


class ExperienciaItem(BaseModel):
    puesto: str
    empresa: str
    descripcion: str
    fecha_desde: datetime
    fecha_hasta: datetime | None = None
    actual: bool = False

    @model_validator(mode="after")
    def _rango_coherente(self):
        if self.fecha_hasta is not None and self.fecha_hasta < self.fecha_desde:
            raise ValueError("fecha_hasta debe ser posterior a fecha_desde")
        return self


class FormacionItem(BaseModel):
    titulo: str
    institucion: str
    descripcion: str | None = None
    fecha_desde: datetime
    fecha_hasta: datetime | None = None
    en_curso: bool = False

    @model_validator(mode="after")
    def _rango_coherente(self):
        if self.fecha_hasta is not None and self.fecha_hasta < self.fecha_desde:
            raise ValueError("fecha_hasta debe ser posterior a fecha_desde")
        return self


class ProyectoItem(BaseModel):
    nombre: str
    descripcion: str
    fecha: datetime | None = None
    link: str | None = None


class CvData(BaseModel):
    experiencia: list[ExperienciaItem] = Field(default_factory=list)
    formacion: list[FormacionItem] = Field(default_factory=list)
    habilidades: list[str] = Field(default_factory=list)
    proyectos: list[ProyectoItem] = Field(default_factory=list)


class Perfil(BaseModel):
    perfil_id: str | None = None
    nombre: str                       # visible a la empresa antes del opt-in
    apellido: str                     # NO visible antes del opt-in
    email: str                        # NO visible antes del opt-in
    telefono: str | None = None       # NO visible antes del opt-in
    password_hash: str | None = None  # nunca se serializa hacia afuera (ver routes/perfiles.py)
    cv_texto_original: str | None = None
    cv_data: CvData = Field(default_factory=CvData)  # visible a la empresa antes del opt-in
    cv_generado_harvard: str | None = None
    busqueda_interes: str | None = None
    embedding: list[float] | None = None
    created_at: datetime | None = None

    #: Campos que sólo se exponen a la empresa cuando el match está confirmado.
    CAMPOS_PRIVADOS: ClassVar[frozenset[str]] = frozenset({"apellido", "email", "telefono"})

    #: Nunca se serializa hacia ningún consumidor de la API, ni siquiera al dueño.
    CAMPOS_INTERNOS: ClassVar[frozenset[str]] = frozenset({"password_hash"})

    @field_validator("email")
    @classmethod
    def _email_valido(cls, v: str) -> str:
        v = v.strip()
        if not _EMAIL_RE.match(v):
            raise ValueError("email inválido")
        return v.lower()

    @field_validator("telefono")
    @classmethod
    def _telefono_valido(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not _TELEFONO_RE.match(v):
            raise ValueError("telefono inválido")
        return v


class PerfilCreate(BaseModel):
    """Schema de entrada para crear perfil (sin campos de servidor)."""
    nombre: str
    apellido: str
    email: str
    password: str
    telefono: str | None = None
    cv_texto_original: str | None = None
    cv_data: CvData = Field(default_factory=CvData)
    busqueda_interes: str | None = None

    @field_validator("email")
    @classmethod
    def _email_valido(cls, v: str) -> str:
        v = v.strip()
        if not _EMAIL_RE.match(v):
            raise ValueError("email inválido")
        return v.lower()

    @field_validator("telefono")
    @classmethod
    def _telefono_valido(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not _TELEFONO_RE.match(v):
            raise ValueError("telefono inválido")
        return v

    @field_validator("password")
    @classmethod
    def _password_valida(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("la contraseña debe tener al menos 8 caracteres")
        return v


class PerfilUpdate(BaseModel):
    """Modelo para actualización parcial de perfil (PUT datos personales)."""
    nombre: str | None = None
    apellido: str | None = None
    email: str | None = None
    telefono: str | None = None
    busqueda_interes: str | None = None
