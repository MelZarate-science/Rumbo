"""
Endpoints de autenticación (backlog 1.1). Login simple, sin OAuth.

POST /auth/login entrega una cookie de sesión `HttpOnly`.
POST /auth/logout limpia la cookie.
GET /auth/session devuelve la sesión actual.

El registro de perfil/empresa (con password) sigue pasando por
POST /perfiles y POST /empresas — no se duplica acá.
"""
from typing import Annotated, Literal

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator

from backend.services.auth import (
    AuthError,
    SESSION_COOKIE_NAME,
    crear_token,
    establecer_cookie_sesion,
    limpiar_cookie_sesion,
    sesion_publica,
    verificar_password,
    verificar_token,
)
from backend.services.firestore_client import listar
from backend.services.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


def _error(status_code: int, mensaje: str, codigo: str):
    raise HTTPException(
        status_code=status_code,
        detail={"error": True, "mensaje": mensaje, "codigo": codigo},
    )


class LoginBody(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=256)
    tipo: Literal["perfil", "empresa"]

    @field_validator("email")
    @classmethod
    def _normalizar_email(cls, value: str) -> str:
        return value.strip().lower()


@router.post("/login")
def login(body: LoginBody, request: Request, response: Response):
    enforce_rate_limit(request, scope="auth_login", max_requests=10, window_seconds=60, actor=body.email)
    coleccion = "perfiles" if body.tipo == "perfil" else "empresas"
    campo_email = "email" if body.tipo == "perfil" else "email_registro"

    candidatos = listar(coleccion, {campo_email: body.email})
    if not candidatos:
        _error(status.HTTP_401_UNAUTHORIZED, "Email o contraseña incorrectos", "CREDENCIALES_INVALIDAS")

    doc = candidatos[0]
    hash_guardado = doc.get("password_hash")
    if not hash_guardado or not verificar_password(body.password, hash_guardado):
        _error(status.HTTP_401_UNAUTHORIZED, "Email o contraseña incorrectos", "CREDENCIALES_INVALIDAS")

    sujeto_id = doc["_document_id"]
    token = crear_token(sujeto_id, body.tipo)
    establecer_cookie_sesion(response, token)
    return {"id": sujeto_id, "tipo": body.tipo}


SessionCookie = Annotated[str | None, Cookie(default=None, alias=SESSION_COOKIE_NAME)]


def usuario_actual(
    session_cookie: SessionCookie = None,
    authorization: str | None = Header(default=None),
) -> dict:
    """
    Dependency de FastAPI: exige cookie de sesión o `Authorization: Bearer`.
    Devuelve {"sub": id, "tipo": "perfil"|"empresa", "exp": ...}.
    """
    token = session_cookie
    if token is None and authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    if not token:
        _error(status.HTTP_401_UNAUTHORIZED, "No hay sesión activa", "NO_AUTENTICADO")
    try:
        return verificar_token(token)
    except AuthError as e:
        _error(status.HTTP_401_UNAUTHORIZED, str(e), "TOKEN_INVALIDO")


@router.post("/logout")
def logout(response: Response):
    limpiar_cookie_sesion(response)
    return {"ok": True}


@router.get("/session")
def session(sesion: dict = Depends(usuario_actual)):
    return sesion_publica(sesion)
