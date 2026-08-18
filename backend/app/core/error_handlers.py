import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import AppError

logger = logging.getLogger("app.errors")

CODE_MAP = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "RESOURCE_NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def _error(
    request: Request,
    *,
    code: str,
    message: str,
    status_code: int,
    details: dict | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code.upper() if code.islower() else code,
                "message": message,
                "details": details or {},
                "request_id": request_id,
            },
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "app_error",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "route": request.url.path,
                "status": exc.status_code,
                "error": exc.code,
            },
        )
        return _error(
            request,
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _error(
            request,
            code="VALIDATION_ERROR",
            message="Request validation failed",
            status_code=422,
            details={"errors": exc.errors()},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error(
            request,
            code=CODE_MAP.get(exc.status_code, "HTTP_ERROR"),
            message=str(exc.detail),
            status_code=exc.status_code,
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "route": request.url.path,
                "status": 500,
                "error": "INTERNAL_ERROR",
            },
        )
        details = {} if settings.is_production else {"type": type(exc).__name__}
        return _error(
            request,
            code="INTERNAL_ERROR",
            message="Internal server error",
            status_code=500,
            details=details,
        )
