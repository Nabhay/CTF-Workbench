from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ctf_workbench import __version__
from ctf_workbench.config import Settings, get_settings


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str
    api: Literal["ok"] = "ok"
    bind: str
    data_root: str
    database: str = Field(description="Redacted URL; connectivity is checked in M0-02.")
    docker_configured: bool
    worker: Literal["separate_process"] = "separate_process"


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        resolved.ensure_data_root()
        yield

    application = FastAPI(
        title="CTF Workbench",
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @application.get("/api/v1/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        current = get_settings()
        return HealthResponse(
            version=__version__,
            bind=f"{current.bind_host}:{current.bind_port}",
            data_root=str(current.data_root.expanduser().resolve()),
            database=current.redacted_database_url(),
            docker_configured=current.docker_host is not None,
        )

    return application


app = create_app()
