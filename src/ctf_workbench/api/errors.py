from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ctf_workbench.domain.errors import ConflictError, WorkbenchError

REQUEST_ID_HEADER = "X-Request-ID"


def request_id_for(request: Request) -> str:
    existing = request.headers.get(REQUEST_ID_HEADER)
    if existing:
        return existing
    return str(uuid4())


def error_body(*, code: str, message: str, request_id: str, details: Any = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details, "request_id": request_id}}


def install_error_handlers(app: FastAPI) -> None:
    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request_id_for(request)
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", request_id_for(request))
        return JSONResponse(
            status_code=409,
            content=error_body(
                code="conflict",
                message=str(exc),
                request_id=request_id,
                details={"current_revision": exc.current_revision},
            ),
            headers={REQUEST_ID_HEADER: request_id},
        )

    @app.exception_handler(WorkbenchError)
    async def domain_handler(request: Request, exc: WorkbenchError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", request_id_for(request))
        return JSONResponse(
            status_code=400,
            content=error_body(code="domain_error", message=str(exc), request_id=request_id),
            headers={REQUEST_ID_HEADER: request_id},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", request_id_for(request))
        code = {
            401: "unauthenticated",
            403: "denied",
            404: "not_found",
            405: "method_not_allowed",
            409: "conflict",
            413: "payload_too_large",
            422: "invalid_input",
            429: "quota",
            503: "unavailable",
        }.get(exc.status_code, "http_error")
        detail = exc.detail if not isinstance(exc.detail, str) else None
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code=code, message=message, request_id=request_id, details=detail),
            headers={REQUEST_ID_HEADER: request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", request_id_for(request))
        return JSONResponse(
            status_code=422,
            content=error_body(
                code="invalid_input",
                message="Request failed validation.",
                request_id=request_id,
                details=exc.errors(),
            ),
            headers={REQUEST_ID_HEADER: request_id},
        )
