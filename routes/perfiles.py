"""
Endpoints de perfiles. Ver `rumbo-contrato-interfaces.md`, sección 3.

POST   /perfiles                        -> crea perfil (1.2)
GET    /perfiles/{perfil_id}            -> devuelve perfil (1.2)
PUT    /perfiles/{perfil_id}            -> edita datos personales (1.2)
PUT    /perfiles/{perfil_id}/cv         -> carga cv_data + regenera embedding (1.3)
POST   /perfiles/{perfil_id}/cv/pdf     -> parsea PDF a cv_data (3.1)
POST   /perfiles/{perfil_id}/cv/generar -> genera CV Harvard (3.2, 3.3)
GET    /perfiles/{perfil_id}/cv/descargar -> PDF descargable (3.4)
GET    /perfiles/{perfil_id}/matches    -> puestos afines, SIN nombre_empresa
                                           salvo estado notificado+ (2.12)
"""
from fastapi import APIRouter

router = APIRouter(prefix="/perfiles", tags=["perfiles"])
