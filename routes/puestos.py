"""
Endpoints de puestos. Ver `rumbo-contrato-interfaces.md`, sección 3.

PUT /puestos/{puesto_id} -> edita puesto. Si cambia `descripcion`, hay que
                            volver a correr la clasificación y extracción (1.5)
"""
from fastapi import APIRouter

router = APIRouter(prefix="/puestos", tags=["puestos"])
