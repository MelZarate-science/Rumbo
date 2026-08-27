"""
Gestión del ciclo de vida de un match y de la visibilidad escalonada.

Esto NO es un agente: no hay razonamiento de modelo, es lógica de negocio.
Cambia estados y controla qué campos se revelan a cada lado.

Ciclo: pendiente -> notificado -> confirmado | rechazado

Backlog: tareas 4.2 a 4.5
"""


def enviar_invitacion(match_id: str) -> dict:
    """
    Acción MANUAL de la empresa. Pasa el match a `notificado` y revela al
    perfil qué empresa lo invitó (antes no lo sabía).
    """
    raise NotImplementedError


def procesar_respuesta(match_id: str, aceptar: bool) -> dict:
    """
    Acción MANUAL del perfil. Si acepta, el match pasa a `confirmado` y recién
    ahí se revelan apellido y contacto a la empresa.
    """
    raise NotImplementedError


def filtrar_campos_visibles(perfil: dict, estado_match: str) -> dict:
    """
    Aplica la regla de visibilidad escalonada sobre un perfil.

    Antes de `confirmado`: nombre de pila, cv_data. Nunca apellido, email ni teléfono.
    """
    raise NotImplementedError
