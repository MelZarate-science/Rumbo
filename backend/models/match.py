"""Modelo de la colección `matches`. Ver `rumbo-schema-bd.md`."""
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class EstadoMatch(str, Enum):
    PENDIENTE = "pendiente"      # el agente calculó el score; nadie hizo nada todavía
    NOTIFICADO = "notificado"    # la empresa invitó (acción manual); el perfil ya sabe qué empresa es
    CONFIRMADO = "confirmado"    # el perfil aceptó; la empresa ve apellido y contacto
    RECHAZADO = "rechazado"      # el perfil no aceptó


class RoadmapItem(BaseModel):
    requisito_id: str
    nombre: str
    cumplido: bool
    porcentaje_mercado: int              # qué % de los puestos del rol lo piden
    especifico_de_esta_empresa: bool     # es particularidad de esta empresa, no estándar del rol
    sugerencia: str | None = None


class Match(BaseModel):
    match_id: str | None = None
    perfil_id: str
    empresa_id: str
    puesto_id: str | None = None
    score: int                           # 0-100
    roadmap: list[RoadmapItem] = Field(default_factory=list)
    justificacion: str
    estado: EstadoMatch = EstadoMatch.PENDIENTE
    created_at: datetime | None = None
    updated_at: datetime | None = None
