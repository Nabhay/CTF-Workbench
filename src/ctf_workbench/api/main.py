from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ctf_workbench import __version__
from ctf_workbench.api.events import router as events_router
from ctf_workbench.config import Settings, get_settings
from ctf_workbench.db.runtime import database_status, get_database, init_database, reset_database


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str
    api: Literal["ok"] = "ok"
    bind: str
    data_root: str
    database: str = Field(description="Redacted database URL")
    database_status: Literal["ok", "unavailable", "unmigrated"]
    docker_configured: bool
    worker: Literal["separate_process"] = "separate_process"


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        resolved.ensure_data_root()
        init_database(resolved)
        yield
        reset_database()

    application = FastAPI(
        title="CTF Workbench",
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    application.include_router(events_router)
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
        try:
            engine = get_database().engine
            db_state = database_status(engine)
        except RuntimeError:
            db_state = "unavailable"
        return HealthResponse(
            version=__version__,
            bind=f"{current.bind_host}:{current.bind_port}",
            data_root=str(current.data_root.expanduser().resolve()),
            database=current.redacted_database_url(),
            database_status=db_state,
            docker_configured=current.docker_host is not None,
        )

    return application


app = create_app()
