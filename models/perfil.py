"""Modelo de la colección `perfiles`. Ver `rumbo-schema-bd.md`."""
from pydantic import BaseModel
from datetime import datetime


class ExperienciaItem(BaseModel):
    puesto: str
    empresa: str
    descripcion: str
    fecha_desde: datetime
    fecha_hasta: datetime | None = None
    actual: bool = False


class FormacionItem(BaseModel):
    titulo: str
    institucion: str
    descripcion: str | None = None
    fecha_desde: datetime
    fecha_hasta: datetime | None = None
    en_curso: bool = False


class ProyectoItem(BaseModel):
    nombre: str
    descripcion: str
    fecha: datetime | None = None
    link: str | None = None


class CvData(BaseModel):
    experiencia: list[ExperienciaItem] = []
    formacion: list[FormacionItem] = []
    habilidades: list[str] = []
    proyectos: list[ProyectoItem] = []


class Perfil(BaseModel):
    perfil_id: str | None = None
    nombre: str                       # visible a la empresa antes del opt-in
    apellido: str                     # NO visible antes del opt-in
    email: str                        # NO visible antes del opt-in
    telefono: str | None = None       # NO visible antes del opt-in
    cv_texto_original: str | None = None
    cv_data: CvData = CvData()        # visible a la empresa antes del opt-in
    cv_generado_harvard: str | None = None
    busqueda_interes: str | None = None
    embedding: list[float] | None = None
    created_at: datetime | None = None
