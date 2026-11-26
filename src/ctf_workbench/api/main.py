from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ctf_workbench import __version__
from ctf_workbench.api.errors import install_error_handlers
from ctf_workbench.api.events import EventRead
from ctf_workbench.api.events import router as events_router
from ctf_workbench.api.refs import router as refs_router
from ctf_workbench.api.ws import router as ws_router
from ctf_workbench.config import Settings, get_settings
from ctf_workbench.db.engine import session_scope
from ctf_workbench.db.runtime import database_status, get_database, init_database, reset_database
from ctf_workbench.services.broker import StreamBroker
from ctf_workbench.services.outbox import dispatch_pending

logger = logging.getLogger(__name__)


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
        broker = StreamBroker()
        _app.state.broker = broker
        stop = asyncio.Event()

        def publish_event(event: object) -> None:
            broker.publish(EventRead.model_validate(event).model_dump(mode="json"))

        async def pump_outbox() -> None:
            while not stop.is_set():
                try:
                    db = get_database()
                    with session_scope(db.sessions) as session:
                        dispatch_pending(session, publish_event)
                except Exception:
                    logger.exception("outbox pump failed")
                try:
                    await asyncio.wait_for(stop.wait(), timeout=0.2)
                except TimeoutError:
                    continue

        pump_task = asyncio.create_task(pump_outbox())
        try:
            yield
        finally:
            stop.set()
            pump_task.cancel()
            reset_database()

    application = FastAPI(
        title="CTF Workbench",
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    install_error_handlers(application)
    application.include_router(events_router)
    application.include_router(refs_router)
    application.include_router(ws_router)
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
