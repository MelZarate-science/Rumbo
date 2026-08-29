"""
Endpoints de puestos. Ver `rumbo-contrato-interfaces.md`, sección 3.

PUT /puestos/{puesto_id} -> edita puesto. Si cambia `descripcion`, hay que
                            volver a correr la clasificación y extracción (1.5)
GET /puestos/{puesto_id} -> devuelve un puesto individual
"""
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from models.puesto import Puesto, PuestoUpdate
from pipeline.matching_pipeline import ejecutar_pipeline_indexado
from services.firestore_client import obtener, actualizar

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
def actualizar_puesto(puesto_id: str, cambios: PuestoUpdate):
    """
    Actualiza un puesto. Si cambia `descripcion` o `titulo`, re-ejecuta el
    pipeline de indexado (clasificación + extracción de requisitos).
    """
    data = obtener("puestos", puesto_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Puesto no encontrado", "PUESTO_NO_ENCONTRADO")

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