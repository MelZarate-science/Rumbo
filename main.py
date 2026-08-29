"""
Entrypoint del servicio. Corre en Cloud Run.
"""
import logging
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from routes import empresas, matches, perfiles, puestos

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Rumbo", version="0.1.0")

app.include_router(perfiles.router)
app.include_router(empresas.router)
app.include_router(puestos.router)
app.include_router(matches.router)


@app.get("/health")
def health():
    """Health check — usado para verificar el despliegue en Cloud Run."""
    return {"status": "ok", "service": "rumbo"}


# ---- Manejo de errores unificado (formato contrato) ----
# {"error": true, "mensaje": str, "codigo": "MAYUSCULAS_CON_GUION_BAJO"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errores = exc.errors()
    # Tomamos el primer error para el mensaje principal
    if errores:
        primer = errores[0]
        loc = " -> ".join(str(x) for x in primer["loc"])
        msg = f"{loc}: {primer['msg']}"
    else:
        msg = "Error de validación"
    return JSONResponse(
        status_code=422,
        content={"error": True, "mensaje": msg, "codigo": "ERROR_VALIDACION"},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Si ya viene con detail dict (nuestro formato), lo usamos tal cual
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    # Sino, formateamos
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