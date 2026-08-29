"""
Endpoints de empresas. Ver `rumbo-contrato-interfaces.md`, sección 3.

POST /empresas                            -> crea empresa (1.4)
GET  /empresas/{empresa_id}               -> devuelve empresa (1.4)
PUT  /empresas/{empresa_id}               -> edita empresa (1.4)
POST /empresas/{empresa_id}/puestos       -> carga puesto + dispara indexado (1.5)
GET  /empresas/{empresa_id}/puestos       -> lista puestos (1.5)
GET  /empresas/{empresa_id}/matches       -> matches de la empresa (visibilidad perfil filtrada)
"""
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from models.empresa import Empresa
from models.puesto import Puesto
from pipeline.matching_pipeline import ejecutar_pipeline_indexado
from services.firestore_client import crear, listar, obtener
from services.invitaciones import filtrar_campos_visibles

router = APIRouter(prefix="/empresas", tags=["empresas"])


def _error(status_code: int, mensaje: str, codigo: str):
    raise HTTPException(
        status_code=status_code,
        detail={"error": True, "mensaje": mensaje, "codigo": codigo},
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def crear_empresa(empresa: Empresa):
    """Crea una empresa. El ID lo genera Firestore."""
    datos = empresa.model_dump(mode="python", exclude_none=True)
    empresa_id = crear("empresas", datos)
    datos["empresa_id"] = empresa_id
    return {"empresa_id": empresa_id, **datos}


@router.get("/{empresa_id}")
def obtener_empresa(empresa_id: str):
    """Devuelve la empresa."""
    data = obtener("empresas", empresa_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Empresa no encontrada", "EMPRESA_NO_ENCONTRADA")
    data["empresa_id"] = empresa_id
    return data


@router.put("/{empresa_id}")
def actualizar_empresa(empresa_id: str, cambios: Empresa):
    """Actualiza datos de la empresa."""
    data = obtener("empresas", empresa_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Empresa no encontrada", "EMPRESA_NO_ENCONTRADA")

    updates = cambios.model_dump(
        mode="python", exclude={"empresa_id", "created_at"}, exclude_none=True
    )
    if not updates:
        _error(status.HTTP_400_BAD_REQUEST, "No hay cambios válidos", "SIN_CAMBIOS")
    updates["updated_at"] = datetime.now(UTC)
    from services.firestore_client import actualizar
    actualizar("empresas", empresa_id, updates)
    data = obtener("empresas", empresa_id)
    data["empresa_id"] = empresa_id
    return data


@router.post("/{empresa_id}/puestos", status_code=status.HTTP_201_CREATED)
def crear_puesto(empresa_id: str, puesto: Puesto):
    """
    Crea un puesto bajo la empresa y dispara el indexado (clasificación + extracción).
    """
    data = obtener("empresas", empresa_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Empresa no encontrada", "EMPRESA_NO_ENCONTRADA")

    datos = puesto.model_dump(mode="python", exclude_none=True)
    datos["empresa_id"] = empresa_id
    puesto_id = crear("puestos", datos)

    # Disparar indexado síncrono
    ejecutar_pipeline_indexado(puesto_id)

    datos["puesto_id"] = puesto_id
    return {"puesto_id": puesto_id, **datos}


@router.get("/{empresa_id}/puestos")
def listar_puestos_empresa(empresa_id: str):
    """Lista los puestos activos de la empresa."""
    data = obtener("empresas", empresa_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Empresa no encontrada", "EMPRESA_NO_ENCONTRADA")

    puestos = listar("puestos", {"empresa_id": empresa_id, "activo": True})
    for p in puestos:
        p["puesto_id"] = p.pop("_document_id")
    return puestos


@router.get("/{empresa_id}/matches")
def listar_matches_empresa(empresa_id: str):
    """
    Lista los matches de los puestos de la empresa.

    Respuesta: perfiles con visibilidad filtrada según estado del match
    (apellido/email/telefono solo si confirmado).
    """
    data = obtener("empresas", empresa_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Empresa no encontrada", "EMPRESA_NO_ENCONTRADA")

    # Obtener puestos de la empresa
    puestos = listar("puestos", {"empresa_id": empresa_id, "activo": True})
    puesto_ids = [p["_document_id"] for p in puestos]

    if not puesto_ids:
        return []

    # Buscar matches de esos puestos
    from services.firestore_client import listar as _listar
    matches = _listar("matches", {"puesto_id": puesto_ids})

    respuesta = []
    for m in matches:
        m["match_id"] = m.pop("_document_id")
        # Cargar perfil
        perfil = obtener("perfiles", m.get("perfil_id"))
        if perfil:
            perfil["perfil_id"] = m["perfil_id"]
            perfil_filtrado = filtrar_campos_visibles(perfil, m["estado"])
            perfil_filtrado.pop("cv_texto_original", None)
            perfil_filtrado.pop("cv_generado_harvard", None)
            perfil_filtrado.pop("embedding", None)
            perfil_filtrado.pop("busqueda_interes", None)
            perfil_filtrado.pop("created_at", None)
        else:
            perfil_filtrado = {}

        # Cargar puesto
        puesto = obtener("puestos", m.get("puesto_id"))
        puesto_info = {"puesto_id": m.get("puesto_id"), "titulo": puesto.get("titulo")} if puesto else {}

        respuesta.append({
            "match_id": m["match_id"],
            "puesto": puesto_info,
            "perfil": perfil_filtrado,
            "score": m.get("score"),
            "estado": m.get("estado"),
            "roadmap": m.get("roadmap", []),
            "justificacion": m.get("justificacion"),
        })
    return respuesta