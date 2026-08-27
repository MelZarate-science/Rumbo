"""
Endpoints de matches — el flujo de invitación con opt-in.
Ver `rumbo-contrato-interfaces.md`, sección 3.

GET  /matches/{match_id}           -> match con visibilidad según estado (2.10)
POST /matches/{match_id}/invitar   -> acción MANUAL de la empresa (4.2)
POST /matches/{match_id}/responder -> acción MANUAL del perfil (4.4)
"""
from fastapi import APIRouter

router = APIRouter(prefix="/matches", tags=["matches"])
