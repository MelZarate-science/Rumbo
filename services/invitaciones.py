"""
Gestión del ciclo de vida de un match y de la visibilidad escalonada.

Esto NO es un agente: no hay razonamiento de modelo, es lógica de negocio.
Cambia estados y controla qué campos se revelan a cada lado.

Ciclo: pendiente -> notificado -> confirmado | rechazado

Reglas de visibilidad:
- El perfil no ve el nombre de la empresa hasta que el match pase de
  `pendiente` (es decir, `notificado`, `confirmado` o `rechazado`).
- La empresa no ve apellido, email ni teléfono del perfil hasta que el
  match esté `confirmado`.

Backlog: tareas 4.2 a 4.5
"""

from datetime import UTC, datetime

from models.match import EstadoMatch
from models.perfil import Perfil
from services.firestore_client import actualizar, obtener


class TransicionInvalidaError(ValueError):
    """La transición pedida no es válida para el estado actual del match."""


def enviar_invitacion(match_id: str) -> dict:
    """
    Acción MANUAL de la empresa. Pasa el match a `notificado` y revela al
    perfil qué empresa lo invitó (antes no lo sabía).
    """
    match = obtener("matches", match_id)
    if match is None:
        raise TransicionInvalidaError("match no encontrado")
    if match["estado"] != EstadoMatch.PENDIENTE.value:
        raise TransicionInvalidaError(
            f"solo se puede invitar un match pendiente (estado actual: {match['estado']})"
        )
    actualizar("matches", match_id, {
        "estado": EstadoMatch.NOTIFICADO.value,
        "updated_at": datetime.now(UTC),
    })
    match["estado"] = EstadoMatch.NOTIFICADO.value
    return match


def procesar_respuesta(match_id: str, aceptar: bool) -> dict:
    """
    Acción MANUAL del perfil. Si acepta, el match pasa a `confirmado` y recién
    ahí se revelan apellido y contacto a la empresa.
    """
    match = obtener("matches", match_id)
    if match is None:
        raise TransicionInvalidaError("match no encontrado")
    if match["estado"] != EstadoMatch.NOTIFICADO.value:
        raise TransicionInvalidaError(
            f"solo se puede responder un match notificado (estado actual: {match['estado']})"
        )
    nuevo_estado = EstadoMatch.CONFIRMADO if aceptar else EstadoMatch.RECHAZADO
    actualizar("matches", match_id, {
        "estado": nuevo_estado.value,
        "updated_at": datetime.now(UTC),
    })
    match["estado"] = nuevo_estado.value
    return match


def filtrar_campos_visibles(perfil: dict, estado_match: str) -> dict:
    """
    Aplica la regla de visibilidad escalonada sobre un perfil.

    Antes de `confirmado`: nombre de pila, cv_data. Nunca apellido, email ni teléfono.
    Devuelve una copia; el dict original no se muta.
    """
    visible = dict(perfil)
    if estado_match != EstadoMatch.CONFIRMADO.value:
        for campo in Perfil.CAMPOS_PRIVADOS:
            visible.pop(campo, None)
    return visible


def es_empresa_visible(estado_match: str) -> bool:
    """El perfil ve qué empresa es (nombre) sólo cuando el match salió de `pendiente`."""
    return estado_match != EstadoMatch.PENDIENTE.value
