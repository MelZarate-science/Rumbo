"""Modelo de la colección `matches`. Ver `rumbo-schema-bd.md`."""
from enum import Enum


class EstadoMatch(str, Enum):
    PENDIENTE = "pendiente"      # el agente calculó el score; nadie hizo nada todavía
    NOTIFICADO = "notificado"    # la empresa invitó (acción manual); el perfil ya sabe qué empresa es
    CONFIRMADO = "confirmado"    # el perfil aceptó; la empresa ve apellido y contacto
    RECHAZADO = "rechazado"      # el perfil no aceptó
