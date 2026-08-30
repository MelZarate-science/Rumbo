"""
Entrypoint real del servicio. Corre en Cloud Run.
"""
import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.routes import auth, empresas, matches, perfiles, puestos

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Rumbo", version="0.1.0")

app.include_router(auth.router)
app.include_router(perfiles.router)
app.include_router(empresas.router)
app.include_router(puestos.router)
app.include_router(matches.router)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_FRONTEND_DIST = _REPO_ROOT / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    app.mount("/app", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")


@app.get("/health")
def health():
    """Health check usado para verificar el despliegue en Cloud Run."""
    return {"status": "ok", "service": "rumbo"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errores = exc.errors()
    if errores:
        primer = errores[0]
        loc = " -> ".join(str(x) for x in primer["loc"])
        msg = f"{loc}: {primer['msg']}"
    else:
        msg = "Error de validacion"
    return JSONResponse(
        status_code=422,
        content={"error": True, "mensaje": msg, "codigo": "ERROR_VALIDACION"},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "mensaje": exc.detail, "codigo": "ERROR_HTTP"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": True, "mensaje": "Error interno del servidor", "codigo": "ERROR_INTERNO"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
