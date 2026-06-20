"""FastAPI application entrypoint.

Run locally:  uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth as auth_router
from app.api import state as state_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Порядок API",
    version="0.1.0",
    summary="Calm personal order — P0 backend (auth + state bundle bridge).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # Bearer tokens (Authorization header), not cookies — so no credentials,
    # which also keeps the "*" origin valid for browsers.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(state_router.router)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"name": "poryadok-backend", "docs": "/docs", "health": "/health"}
