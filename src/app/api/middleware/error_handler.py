import logging
from typing import cast

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.schemas import ApiResponse, format_http_status
from app.application.common.exceptions import (
    Conflict,
    InvalidInput,
    NotFound,
    Unauthorized,
)

logger = logging.getLogger(__name__)


def _error(status: int, message: str, data: object | None = None) -> JSONResponse:
    body = ApiResponse[object](
        message=message,
        status=format_http_status(status),
        data=data,
    )
    return JSONResponse(status_code=status, content=jsonable_encoder(body))


async def handle_http_exception(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    http_exception = cast(StarletteHTTPException, exception)
    message = (
        http_exception.detail if isinstance(http_exception.detail, str) else "HTTP error"
    )
    return _error(http_exception.status_code, message)


async def handle_validation_exception(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    validation_error = cast(RequestValidationError, exception)
    errors = [
        {key: value for key, value in error.items() if key != "ctx"}
        for error in validation_error.errors()
    ]
    return _error(422, "Request validation failed", errors)


async def handle_unexpected_exception(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled application error request_id=%s",
        getattr(request.state, "request_id", None),
    )
    return _error(500, "Internal server error")


async def handle_not_found(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    return _error(404, str(exception))


async def handle_invalid_input(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    return _error(422, str(exception))


async def handle_conflict(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    return _error(409, str(exception))


async def handle_unauthorized(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    response = _error(401, str(exception))
    response.headers["WWW-Authenticate"] = "Bearer"
    return response


def register_error_handlers(application: FastAPI) -> None:
    application.add_exception_handler(StarletteHTTPException, handle_http_exception)
    application.add_exception_handler(
        RequestValidationError,
        handle_validation_exception,
    )
    application.add_exception_handler(Exception, handle_unexpected_exception)
    application.add_exception_handler(NotFound, handle_not_found)
    application.add_exception_handler(InvalidInput, handle_invalid_input)
    application.add_exception_handler(Conflict, handle_conflict)
    application.add_exception_handler(Unauthorized, handle_unauthorized)
