"""
Endpoints de puestos. Ver `rumbo-contrato-interfaces.md`, sección 3.

PUT /puestos/{puesto_id} -> edita puesto. Si cambia `descripcion`, hay que
                            volver a correr la clasificación y extracción (1.5)
GET /puestos/{puesto_id} -> devuelve un puesto individual
"""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from backend.models.puesto import Puesto, PuestoUpdate
from backend.pipeline.matching_pipeline import ejecutar_pipeline_indexado
from backend.routes.auth import usuario_actual
from backend.services.firestore_client import obtener, actualizar

router = APIRouter(prefix="/puestos", tags=["puestos"])


def _error(status_code: int, mensaje: str, codigo: str):
    raise HTTPException(
        status_code=status_code,
        detail={"error": True, "mensaje": mensaje, "codigo": codigo},
    )


@router.get("/{puesto_id}")
def obtener_puesto(puesto_id: str):
    """Devuelve un puesto por ID."""
    data = obtener("puestos", puesto_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Puesto no encontrado", "PUESTO_NO_ENCONTRADO")
    data["puesto_id"] = puesto_id
    return data


@router.put("/{puesto_id}")
def actualizar_puesto(puesto_id: str, cambios: PuestoUpdate, sesion: dict = Depends(usuario_actual)):
    """
    Actualiza un puesto. Si cambia `descripcion` o `titulo`, re-ejecuta el
    pipeline de indexado (clasificación + extracción de requisitos).
    Requiere sesión de la empresa dueña del puesto.
    """
    data = obtener("puestos", puesto_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Puesto no encontrado", "PUESTO_NO_ENCONTRADO")
    if sesion["tipo"] != "empresa" or sesion["sub"] != data.get("empresa_id"):
        _error(status.HTTP_403_FORBIDDEN, "No podés modificar un puesto que no es tuyo", "NO_AUTORIZADO")

    updates = cambios.model_dump(mode="python", exclude_none=True)
    if not updates:
        _error(status.HTTP_400_BAD_REQUEST, "No hay cambios válidos", "SIN_CAMBIOS")

    descripcion_cambio = "descripcion" in updates or "titulo" in updates
    updates["updated_at"] = datetime.now(UTC)
    actualizar("puestos", puesto_id, updates)

    if descripcion_cambio:
        # Re-ejecutar indexado completo
        ejecutar_pipeline_indexado(puesto_id)

    data = obtener("puestos", puesto_id)
    data["puesto_id"] = puesto_id
    return data
