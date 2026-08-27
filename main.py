"""
Entrypoint del servicio. Corre en Cloud Run.
"""
import os

from fastapi import FastAPI

from routes import perfiles, empresas, puestos, matches

app = FastAPI(title="Rumbo", version="0.1.0")

app.include_router(perfiles.router)
app.include_router(empresas.router)
app.include_router(puestos.router)
app.include_router(matches.router)


@app.get("/health")
def health():
    """Health check — usado para verificar el despliegue en Cloud Run."""
    return {"status": "ok", "service": "rumbo"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
