"""Unified error envelope.

Every error response (validation, not-found, auth, upstream failure, unhandled
exception) funnels through this module so the API always returns exactly:

    {"success": false, "error": {"code": "...", "message": "...", "details": []}}

matching packages/shared/src/types/api.ts::ApiErrorResponse.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("firip.errors")


class ApiError(Exception):
    """Raised by application code to produce a specific error envelope.

    Prefer raising this (or a subclass) over a bare HTTPException so the
    error `code` is explicit and stable for API consumers.
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


class NotFoundError(ApiError):
    def __init__(self, message: str = "Resource not found", details: list | None = None) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, "not_found", message, details)


class UnauthorizedError(ApiError):
    def __init__(self, message: str = "Authentication required", details: list | None = None) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, "unauthorized", message, details)


class ForbiddenError(ApiError):
    def __init__(self, message: str = "Insufficient permissions", details: list | None = None) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, "forbidden", message, details)


class UpstreamError(ApiError):
    def __init__(self, message: str = "Upstream data source failure", details: list | None = None) -> None:
        super().__init__(status.HTTP_503_SERVICE_UNAVAILABLE, "upstream_unavailable", message, details)


def _envelope(code: str, message: str, details: list) -> dict:
    return {"success": False, "error": {"code": code, "message": message, "details": details}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope("validation_error", "Request validation failed", exc.errors()),
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_request: Request, exc: HTTPException) -> JSONResponse:
        code = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
            409: "conflict",
            422: "validation_error",
            429: "rate_limited",
            503: "upstream_unavailable",
        }.get(exc.status_code, "http_error")
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Request failed"
        details = [] if isinstance(detail, str) or detail is None else [detail]
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(code, message, details),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope("internal_error", "An unexpected error occurred", []),
        )
