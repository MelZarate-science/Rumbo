"""
Endpoints de matches — el flujo de invitación con opt-in.
Ver `rumbo-contrato-interfaces.md`, sección 3.

GET  /matches/{match_id}           -> match con visibilidad según estado (2.10)
POST /matches/{match_id}/invitar   -> acción MANUAL de la empresa (4.2)
POST /matches/{match_id}/responder -> acción MANUAL del perfil (4.4)
"""
from fastapi import APIRouter, Depends, HTTPException, status

from backend.models.match import EstadoMatch
from backend.routes.auth import usuario_actual
from backend.services.firestore_client import obtener
from backend.services.invitaciones import (
    TransicionInvalidaError,
    enviar_invitacion,
    filtrar_campos_visibles,
    procesar_respuesta,
)

router = APIRouter(prefix="/matches", tags=["matches"])


def _error(status_code: int, mensaje: str, codigo: str):
    raise HTTPException(
        status_code=status_code,
        detail={"error": True, "mensaje": mensaje, "codigo": codigo},
    )


@router.get("/{match_id}")
def obtener_match(match_id: str):
    """
    Devuelve el match con visibilidad según quién consulta:
    - Si el perfil consulta (estado pendiente): sin empresa_nombre.
    - Si la empresa consulta: perfil filtrado según estado.
    Para MVP, la ruta es pública y decide visibilidad combinada:
      * empresa: siempre visible (la empresa conoce su propio nombre)
      * perfil: solo visible si estado != pendiente
      * campos privados del perfil: solo si confirmado
    """
    match = obtener("matches", match_id)
    if match is None:
        _error(status.HTTP_404_NOT_FOUND, "Match no encontrado", "MATCH_NO_ENCONTRADO")

    match["match_id"] = match_id

    # Cargar empresa
    empresa = obtener("empresas", match.get("empresa_id")) if match.get("empresa_id") else None
    empresa_info = {"empresa_id": match.get("empresa_id"), "nombre": empresa.get("nombre_empresa")} if empresa else {}

    # Cargar puesto
    puesto = obtener("puestos", match.get("puesto_id")) if match.get("puesto_id") else None
    puesto_info = {"puesto_id": match.get("puesto_id"), "titulo": puesto.get("titulo")} if puesto else {}

    # Cargar perfil con filtrado
    perfil = obtener("perfiles", match.get("perfil_id")) if match.get("perfil_id") else None
    if perfil:
        perfil["perfil_id"] = match["perfil_id"]
        perfil_filtrado = filtrar_campos_visibles(perfil, match["estado"])
        perfil_filtrado.pop("cv_texto_original", None)
        perfil_filtrado.pop("cv_generado_harvard", None)
        perfil_filtrado.pop("embedding", None)
        perfil_filtrado.pop("busqueda_interes", None)
        perfil_filtrado.pop("created_at", None)
        perfil_filtrado.pop("password_hash", None)
    else:
        perfil_filtrado = {}

    # Visibilidad de empresa para el perfil
    from backend.services.invitaciones import es_empresa_visible
    if es_empresa_visible(match["estado"]):
        empresa_para_perfil = empresa_info
    else:
        empresa_para_perfil = {"empresa_id": match.get("empresa_id"), "nombre": None}

    return {
        "match_id": match["match_id"],
        "empresa": empresa_info,
        "empresa_para_perfil": empresa_para_perfil,
        "puesto": puesto_info,
        "perfil": perfil_filtrado,
        "score": match.get("score"),
        "estado": match.get("estado"),
        "roadmap": match.get("roadmap", []),
        "justificacion": match.get("justificacion"),
        "created_at": match.get("created_at"),
        "updated_at": match.get("updated_at"),
    }


@router.post("/{match_id}/invitar")
def invitar_match(match_id: str, sesion: dict = Depends(usuario_actual)):
    """
    Acción MANUAL de la empresa: invita al perfil.
    Cambia estado pendiente -> notificado. Requiere sesión de la empresa dueña.
    """
    match_actual = obtener("matches", match_id)
    if match_actual is None:
        _error(status.HTTP_404_NOT_FOUND, "Match no encontrado", "MATCH_NO_ENCONTRADO")
    if sesion["tipo"] != "empresa" or sesion["sub"] != match_actual.get("empresa_id"):
        _error(status.HTTP_403_FORBIDDEN, "No podés invitar sobre un match que no es tuyo", "NO_AUTORIZADO")

    try:
        match = enviar_invitacion(match_id)
    except TransicionInvalidaError as e:
        _error(status.HTTP_400_BAD_REQUEST, str(e), "TRANSICION_INVALIDA")
    match["match_id"] = match_id
    return match


@router.post("/{match_id}/responder")
def responder_match(match_id: str, body: dict, sesion: dict = Depends(usuario_actual)):
    """
    Acción MANUAL del perfil: acepta o rechaza la invitación.
    Cambia estado notificado -> confirmado | rechazado. Requiere sesión del perfil dueño.
    """
    match_actual = obtener("matches", match_id)
    if match_actual is None:
        _error(status.HTTP_404_NOT_FOUND, "Match no encontrado", "MATCH_NO_ENCONTRADO")
    if sesion["tipo"] != "perfil" or sesion["sub"] != match_actual.get("perfil_id"):
        _error(status.HTTP_403_FORBIDDEN, "No podés responder un match que no es tuyo", "NO_AUTORIZADO")

    aceptar = body.get("aceptar")
    if not isinstance(aceptar, bool):
        _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Campo 'aceptar' (bool) requerido", "ERROR_VALIDACION")

    try:
        match = procesar_respuesta(match_id, aceptar)
    except TransicionInvalidaError as e:
        _error(status.HTTP_400_BAD_REQUEST, str(e), "TRANSICION_INVALIDA")
    match["match_id"] = match_id
    return match
