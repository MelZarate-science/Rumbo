"""
Endpoints de autenticación (backlog 1.1). Login simple, sin OAuth.

POST /auth/login -> {email, password, tipo: "perfil"|"empresa"} -> {token, id, tipo}

El registro de perfil/empresa (con password) sigue pasando por
POST /perfiles y POST /empresas — no se duplica acá.
"""
from typing import Literal

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from backend.services.auth import AuthError, crear_token, verificar_password, verificar_token
from backend.services.firestore_client import listar

router = APIRouter(prefix="/auth", tags=["auth"])


def _error(status_code: int, mensaje: str, codigo: str):
    raise HTTPException(
        status_code=status_code,
        detail={"error": True, "mensaje": mensaje, "codigo": codigo},
    )


class LoginBody(BaseModel):
    email: str
    password: str
    tipo: Literal["perfil", "empresa"]


@router.post("/login")
def login(body: LoginBody):
    coleccion = "perfiles" if body.tipo == "perfil" else "empresas"
    campo_email = "email" if body.tipo == "perfil" else "email_registro"

    candidatos = listar(coleccion, {campo_email: body.email.strip().lower()})
    if not candidatos:
        _error(status.HTTP_401_UNAUTHORIZED, "Email o contraseña incorrectos", "CREDENCIALES_INVALIDAS")

    doc = candidatos[0]
    hash_guardado = doc.get("password_hash")
    if not hash_guardado or not verificar_password(body.password, hash_guardado):
        _error(status.HTTP_401_UNAUTHORIZED, "Email o contraseña incorrectos", "CREDENCIALES_INVALIDAS")

    sujeto_id = doc["_document_id"]
    token = crear_token(sujeto_id, body.tipo)
    return {"token": token, "id": sujeto_id, "tipo": body.tipo}


def usuario_actual(authorization: str | None = Header(default=None)) -> dict:
    """
    Dependency de FastAPI: exige `Authorization: Bearer <token>` válido.
    Devuelve {"sub": id, "tipo": "perfil"|"empresa", "exp": ...}.
    """
    if not authorization or not authorization.startswith("Bearer "):
        _error(status.HTTP_401_UNAUTHORIZED, "Falta el header Authorization", "NO_AUTENTICADO")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verificar_token(token)
    except AuthError as e:
        _error(status.HTTP_401_UNAUTHORIZED, str(e), "TOKEN_INVALIDO")
