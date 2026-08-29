"""
Endpoints de perfiles. Ver `rumbo-contrato-interfaces.md`, sección 3.

POST   /perfiles                        -> crea perfil (1.2) + devuelve token de sesión (1.1)
GET    /perfiles/{perfil_id}            -> devuelve perfil (1.2)
PUT    /perfiles/{perfil_id}            -> edita datos personales (1.2), requiere sesión propia
PUT    /perfiles/{perfil_id}/cv         -> carga cv_data + dispara matching (1.3), requiere sesión propia
POST   /perfiles/{perfil_id}/cv/pdf     -> parsea PDF a cv_data (3.1) [Fase 3]
POST   /perfiles/{perfil_id}/cv/generar -> genera CV Harvard (3.2) [Fase 3]
GET    /perfiles/{perfil_id}/cv/descargar -> PDF descargable (3.4) [Fase 3]
GET    /perfiles/{perfil_id}/matches    -> puestos afines, SIN nombre_empresa
                                           salvo estado notificado+ (2.12)
"""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from models.perfil import CvData, Perfil, PerfilCreate, PerfilUpdate
from pipeline.matching_pipeline import ejecutar_pipeline_matching
from routes.auth import usuario_actual
from services.auth import crear_token, hashear_password
from services.firestore_client import crear, listar, obtener

router = APIRouter(prefix="/perfiles", tags=["perfiles"])


def _error(status_code: int, mensaje: str, codigo: str):
    raise HTTPException(
        status_code=status_code,
        detail={"error": True, "mensaje": mensaje, "codigo": codigo},
    )


def _sin_internos(data: dict) -> dict:
    return {k: v for k, v in data.items() if k not in Perfil.CAMPOS_INTERNOS}


def _requiere_dueno(perfil_id: str, sesion: dict) -> None:
    if sesion["tipo"] != "perfil" or sesion["sub"] != perfil_id:
        _error(status.HTTP_403_FORBIDDEN, "No podés modificar un perfil que no es el tuyo", "NO_AUTORIZADO")


@router.post("", status_code=status.HTTP_201_CREATED)
def crear_perfil(perfil: PerfilCreate):
    """Crea un perfil y devuelve un token de sesión (login automático al registrarse)."""
    datos = perfil.model_dump(mode="python", exclude_none=True)
    datos["password_hash"] = hashear_password(datos.pop("password"))
    datos["created_at"] = datetime.now(UTC)
    perfil_id = crear("perfiles", datos)
    respuesta = _sin_internos(datos)
    respuesta["perfil_id"] = perfil_id
    respuesta["token"] = crear_token(perfil_id, "perfil")
    return {"perfil_id": perfil_id, **respuesta}


@router.get("/{perfil_id}")
def obtener_perfil(perfil_id: str):
    """Devuelve el perfil completo (vista propietario)."""
    data = obtener("perfiles", perfil_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Perfil no encontrado", "PERFIL_NO_ENCONTRADO")
    data["perfil_id"] = perfil_id
    return _sin_internos(data)


@router.put("/{perfil_id}")
def actualizar_perfil(perfil_id: str, cambios: PerfilUpdate, sesion: dict = Depends(usuario_actual)):
    """Actualiza datos personales (no cv_data; usar PUT /cv para eso). Requiere sesión propia."""
    _requiere_dueno(perfil_id, sesion)
    data = obtener("perfiles", perfil_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Perfil no encontrado", "PERFIL_NO_ENCONTRADO")

    updates = cambios.model_dump(mode="python", exclude_none=True)
    if not updates:
        _error(status.HTTP_400_BAD_REQUEST, "No hay cambios válidos", "SIN_CAMBIOS")
    updates["updated_at"] = datetime.now(UTC)
    from services.firestore_client import actualizar
    actualizar("perfiles", perfil_id, updates)
    data = obtener("perfiles", perfil_id)
    data["perfil_id"] = perfil_id
    return _sin_internos(data)


@router.put("/{perfil_id}/cv")
def actualizar_cv(perfil_id: str, cv: CvData, sesion: dict = Depends(usuario_actual)):
    """
    Carga/actualiza cv_data y dispara el pipeline de matching. Requiere sesión propia.

    Returns:
        perfil actualizado + lista de match_id creados.
    """
    _requiere_dueno(perfil_id, sesion)
    data = obtener("perfiles", perfil_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Perfil no encontrado", "PERFIL_NO_ENCONTRADO")

    updates = cv.model_dump(mode="python", exclude_none=True)
    updates["updated_at"] = datetime.now(UTC)
    from services.firestore_client import actualizar
    actualizar("perfiles", perfil_id, updates)

    # Disparar matching (síncrono en MVP)
    match_ids = ejecutar_pipeline_matching(perfil_id)

    data = obtener("perfiles", perfil_id)
    data["perfil_id"] = perfil_id
    return {"perfil": _sin_internos(data), "matches_creados": match_ids}


@router.get("/{perfil_id}/matches")
def listar_matches_perfil(perfil_id: str):
    """
    Lista los matches del perfil.

    Respuesta: sin nombre de empresa mientras el estado sea `pendiente`.
    """
    data = obtener("perfiles", perfil_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Perfil no encontrado", "PERFIL_NO_ENCONTRADO")

    matches = listar("matches", {"perfil_id": perfil_id})
    respuesta = []
    for m in matches:
        m["match_id"] = m.pop("_document_id")
        # Cargar puesto para el título
        puesto = obtener("puestos", m.get("puesto_id"))
        puesto_titulo = puesto.get("titulo") if puesto else "Desconocido"
        empresa_visible = m["estado"] != "pendiente"
        empresa_nombre = None
        if empresa_visible and m.get("empresa_id"):
            emp = obtener("empresas", m["empresa_id"])
            if emp:
                empresa_nombre = emp.get("nombre_empresa")
        respuesta.append({
            "match_id": m["match_id"],
            "puesto_id": m.get("puesto_id"),
            "puesto_titulo": puesto_titulo,
            "score": m.get("score"),
            "estado": m.get("estado"),
            "roadmap": m.get("roadmap", []),
            "justificacion": m.get("justificacion"),
            "empresa_nombre": empresa_nombre,
        })
    return respuesta


# --- Endpoints Fase 3 (stubs documentados, no implementados en MVP) ---

@router.post("/{perfil_id}/cv/pdf", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def parsear_pdf_cv(perfil_id: str):
    """Parsea PDF a cv_data (Fase 3)."""
    return {"error": True, "mensaje": "No implementado en MVP", "codigo": "NO_IMPLEMENTADO"}


@router.post("/{perfil_id}/cv/generar", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def generar_cv_harvard_endpoint(perfil_id: str):
    """Genera CV formato Harvard (Fase 3)."""
    return {"error": True, "mensaje": "No implementado en MVP", "codigo": "NO_IMPLEMENTADO"}


@router.get("/{perfil_id}/cv/descargar", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def descargar_cv_pdf(perfil_id: str):
    """Descarga PDF del CV (Fase 3)."""
    return {"error": True, "mensaje": "No implementado en MVP", "codigo": "NO_IMPLEMENTADO"}
