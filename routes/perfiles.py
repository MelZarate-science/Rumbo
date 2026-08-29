"""
Endpoints de perfiles. Ver `rumbo-contrato-interfaces.md`, sección 3.

POST   /perfiles                        -> crea perfil (1.2)
GET    /perfiles/{perfil_id}            -> devuelve perfil (1.2)
PUT    /perfiles/{perfil_id}            -> edita datos personales (1.2)
PUT    /perfiles/{perfil_id}/cv         -> carga cv_data + dispara matching (1.3)
POST   /perfiles/{perfil_id}/cv/pdf     -> parsea PDF a cv_data (3.1) [Fase 3]
POST   /perfiles/{perfil_id}/cv/generar -> genera CV Harvard (3.2) [Fase 3]
GET    /perfiles/{perfil_id}/cv/descargar -> PDF descargable (3.4) [Fase 3]
GET    /perfiles/{perfil_id}/matches    -> puestos afines, SIN nombre_empresa
                                           salvo estado notificado+ (2.12)
"""
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from models.perfil import CvData, Perfil, PerfilUpdate
from pipeline.matching_pipeline import ejecutar_pipeline_matching
from services.firestore_client import crear, listar, obtener

router = APIRouter(prefix="/perfiles", tags=["perfiles"])


def _error(status_code: int, mensaje: str, codigo: str):
    raise HTTPException(
        status_code=status_code,
        detail={"error": True, "mensaje": mensaje, "codigo": codigo},
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def crear_perfil(perfil: Perfil):
    """Crea un perfil. El ID lo genera Firestore; devuelve el perfil con ID."""
    datos = perfil.model_dump(mode="python", exclude_none=True)
    perfil_id = crear("perfiles", datos)
    datos["perfil_id"] = perfil_id
    return {"perfil_id": perfil_id, **datos}


@router.get("/{perfil_id}")
def obtener_perfil(perfil_id: str):
    """Devuelve el perfil completo (vista propietario)."""
    data = obtener("perfiles", perfil_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Perfil no encontrado", "PERFIL_NO_ENCONTRADO")
    data["perfil_id"] = perfil_id
    return data


@router.put("/{perfil_id}")
def actualizar_perfil(perfil_id: str, cambios: PerfilUpdate):
    """Actualiza datos personales (no cv_data; usar PUT /cv para eso)."""
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
    return data


@router.put("/{perfil_id}/cv")
def actualizar_cv(perfil_id: str, cv: CvData):
    """
    Carga/actualiza cv_data y dispara el pipeline de matching.

    Returns:
        perfil actualizado + lista de match_id creados.
    """
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
    return {"perfil": data, "matches_creados": match_ids}


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