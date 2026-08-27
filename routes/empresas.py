"""
Endpoints de empresas. Ver `rumbo-contrato-interfaces.md`, sección 3.

POST /empresas                            -> crea empresa (1.4)
GET  /empresas/{empresa_id}               -> devuelve empresa (1.4)
PUT  /empresas/{empresa_id}               -> edita empresa (1.4)
POST /empresas/{empresa_id}/puestos       -> carga puesto (1.5)
GET  /empresas/{empresa_id}/puestos       -> lista puestos (1.5)
GET  /empresas/{empresa_id}/mapa-perfiles -> perfiles afines, SIN apellido
                                             ni contacto salvo confirmado (4.1)
"""
from fastapi import APIRouter

router = APIRouter(prefix="/empresas", tags=["empresas"])
