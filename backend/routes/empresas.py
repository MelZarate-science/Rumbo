"""
Endpoints de empresas. Ver `rumbo-contrato-interfaces.md`, sección 3.

POST /empresas                            -> crea empresa (1.4) + setea cookie de sesión (1.1)
GET  /empresas/{empresa_id}               -> devuelve empresa (1.4), requiere sesión propia
PUT  /empresas/{empresa_id}               -> edita empresa (1.4), requiere sesión propia
POST /empresas/{empresa_id}/puestos       -> carga puesto + dispara indexado (1.5), requiere sesión propia
GET  /empresas/{empresa_id}/puestos       -> lista puestos (1.5)
GET  /empresas/{empresa_id}/mapa-perfiles -> matches de la empresa, ?puesto_id= opcional (4.1)
"""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from backend.models.empresa import Empresa, EmpresaCreate, EmpresaUpdate
from backend.models.puesto import Puesto, PuestoCreate
from backend.pipeline.matching_pipeline import ejecutar_pipeline_indexado
from backend.routes.auth import usuario_actual
from backend.services.auth import crear_token, establecer_cookie_sesion, hashear_password
from backend.services.firestore_client import crear, listar, obtener
from backend.services.invitaciones import filtrar_campos_visibles
from backend.services.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/empresas", tags=["empresas"])


def _error(status_code: int, mensaje: str, codigo: str):
    raise HTTPException(
        status_code=status_code,
        detail={"error": True, "mensaje": mensaje, "codigo": codigo},
    )


def _sin_internos(data: dict) -> dict:
    return {k: v for k, v in data.items() if k not in Empresa.CAMPOS_INTERNOS}


def _requiere_dueno(empresa_id: str, sesion: dict) -> None:
    if sesion["tipo"] != "empresa" or sesion["sub"] != empresa_id:
        _error(status.HTTP_403_FORBIDDEN, "No podés acceder a una empresa que no es la tuya", "NO_AUTORIZADO")


@router.post("", status_code=status.HTTP_201_CREATED)
def crear_empresa(empresa: EmpresaCreate, request: Request, response: Response):
    """Crea una empresa y abre sesión con cookie HttpOnly."""
    enforce_rate_limit(request, scope="registro_empresa", max_requests=5, window_seconds=60, actor=empresa.email_registro)
    if listar("empresas", {"email_registro": empresa.email_registro}):
        _error(status.HTTP_409_CONFLICT, "Ya existe una cuenta con ese email", "EMAIL_YA_REGISTRADO")

    datos = empresa.model_dump(mode="python", exclude_none=True)
    datos["password_hash"] = hashear_password(datos.pop("password"))
    datos["created_at"] = datetime.now(UTC)
    datos["activa"] = True
    empresa_id = crear("empresas", datos)
    respuesta = _sin_internos(datos)
    respuesta["empresa_id"] = empresa_id
    respuesta["tipo"] = "empresa"
    establecer_cookie_sesion(response, crear_token(empresa_id, "empresa"))
    return {"empresa_id": empresa_id, **respuesta}


@router.get("/{empresa_id}")
def obtener_empresa(empresa_id: str, sesion: dict = Depends(usuario_actual)):
    """Devuelve la empresa."""
    _requiere_dueno(empresa_id, sesion)
    data = obtener("empresas", empresa_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Empresa no encontrada", "EMPRESA_NO_ENCONTRADA")
    data["empresa_id"] = empresa_id
    return _sin_internos(data)


@router.put("/{empresa_id}")
def actualizar_empresa(empresa_id: str, cambios: EmpresaUpdate, sesion: dict = Depends(usuario_actual)):
    """Actualiza datos de la empresa. Requiere sesión propia."""
    _requiere_dueno(empresa_id, sesion)
    data = obtener("empresas", empresa_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Empresa no encontrada", "EMPRESA_NO_ENCONTRADA")

    updates = cambios.model_dump(mode="python", exclude_none=True)
    if not updates:
        _error(status.HTTP_400_BAD_REQUEST, "No hay cambios válidos", "SIN_CAMBIOS")
    updates["updated_at"] = datetime.now(UTC)
    from backend.services.firestore_client import actualizar
    actualizar("empresas", empresa_id, updates)
    data = obtener("empresas", empresa_id)
    data["empresa_id"] = empresa_id
    return _sin_internos(data)


@router.post("/{empresa_id}/puestos", status_code=status.HTTP_201_CREATED)
def crear_puesto(empresa_id: str, puesto: PuestoCreate, sesion: dict = Depends(usuario_actual)):
    """
    Crea un puesto bajo la empresa y dispara el indexado (clasificación + extracción).
    Requiere sesión propia.
    """
    _requiere_dueno(empresa_id, sesion)
    data = obtener("empresas", empresa_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Empresa no encontrada", "EMPRESA_NO_ENCONTRADA")

    datos = puesto.model_dump(mode="python", exclude_none=True)
    datos["empresa_id"] = empresa_id
    datos["created_at"] = datetime.now(UTC)
    datos["activo"] = True
    puesto_id = crear("puestos", datos)

    # Disparar indexado síncrono
    ejecutar_pipeline_indexado(puesto_id)

    datos["puesto_id"] = puesto_id
    return {"puesto_id": puesto_id, **datos}


@router.get("/{empresa_id}/puestos")
def listar_puestos_empresa(empresa_id: str, sesion: dict = Depends(usuario_actual)):
    """Lista los puestos activos de la empresa."""
    _requiere_dueno(empresa_id, sesion)
    data = obtener("empresas", empresa_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Empresa no encontrada", "EMPRESA_NO_ENCONTRADA")

    puestos = listar("puestos", {"empresa_id": empresa_id, "activo": True})
    for p in puestos:
        p["puesto_id"] = p.pop("_document_id")
    return puestos


@router.get("/{empresa_id}/mapa-perfiles")
def mapa_perfiles_empresa(empresa_id: str, puesto_id: str | None = None, sesion: dict = Depends(usuario_actual)):
    """
    Mapa de perfiles afines a los puestos de la empresa (backlog 4.1).

    `puesto_id` (opcional): acota el mapa a los matches de ese puesto puntual.
    Respuesta: perfiles con visibilidad filtrada según estado del match
    (apellido/email/telefono solo si confirmado).
    """
    _requiere_dueno(empresa_id, sesion)
    data = obtener("empresas", empresa_id)
    if data is None:
        _error(status.HTTP_404_NOT_FOUND, "Empresa no encontrada", "EMPRESA_NO_ENCONTRADA")

    if puesto_id is not None:
        puesto_ids = [puesto_id]
    else:
        puestos = listar("puestos", {"empresa_id": empresa_id, "activo": True})
        puesto_ids = [p["_document_id"] for p in puestos]

    if not puesto_ids:
        return []

    # Buscar matches de esos puestos
    from backend.services.firestore_client import listar as _listar
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
            perfil_filtrado.pop("password_hash", None)
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
