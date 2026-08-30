"""Compatibility entrypoint that re-exports the backend app."""

import os

from backend.main import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
