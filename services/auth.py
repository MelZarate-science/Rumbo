"""
Autenticación básica (backlog 1.1): sin OAuth, hash de contraseña +
token firmado con HMAC. Alcanza para que un perfil o empresa inicie
sesión y mantenga su sesión activa — no hace falta más para el MVP.

Backlog: tarea 1.1
"""

import base64
import hashlib
import hmac
import json
import os
import time

_ITERACIONES_PBKDF2 = 200_000
_TOKEN_TTL_SEGUNDOS = 60 * 60 * 24 * 7  # 7 días


class AuthError(ValueError):
    """Credenciales inválidas o token inválido/expirado."""


def _secret() -> bytes:
    secreto = os.getenv("AUTH_SECRET_KEY")
    if not secreto:
        raise RuntimeError("AUTH_SECRET_KEY no está seteada")
    return secreto.encode("utf-8")


def hashear_password(password: str) -> str:
    """Devuelve `salt$hash` en hex, usando PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    derivado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERACIONES_PBKDF2)
    return f"{salt.hex()}${derivado.hex()}"


def verificar_password(password: str, hash_guardado: str) -> bool:
    try:
        salt_hex, derivado_hex = hash_guardado.split("$")
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    derivado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERACIONES_PBKDF2)
    return hmac.compare_digest(derivado.hex(), derivado_hex)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_decode(data: str) -> bytes:
    relleno = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + relleno)


def crear_token(sujeto_id: str, tipo: str) -> str:
    """
    `tipo` es "perfil" o "empresa" — el token identifica quién sos y como qué.
    """
    payload = {"sub": sujeto_id, "tipo": tipo, "exp": int(time.time()) + _TOKEN_TTL_SEGUNDOS}
    cuerpo = _b64(json.dumps(payload).encode("utf-8"))
    firma = _b64(hmac.new(_secret(), cuerpo.encode("ascii"), hashlib.sha256).digest())
    return f"{cuerpo}.{firma}"


def verificar_token(token: str) -> dict:
    """Devuelve el payload ({sub, tipo, exp}) si el token es válido y no expiró."""
    try:
        cuerpo, firma = token.split(".")
    except ValueError:
        raise AuthError("token con formato inválido") from None

    firma_esperada = _b64(hmac.new(_secret(), cuerpo.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(firma, firma_esperada):
        raise AuthError("firma de token inválida")

    payload = json.loads(_b64_decode(cuerpo))
    if payload["exp"] < time.time():
        raise AuthError("token expirado")
    return payload
