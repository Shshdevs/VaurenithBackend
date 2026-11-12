import logging
from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.schemas import ApiResponse, ResponseCode, format_http_status
from app.api.schemas.v1.synchronization import ChangeLogResyncRequired
from app.application.common.exceptions import (
    ChangeLogCursorExpired,
    Conflict,
    InvalidInput,
    NotFound,
    Unauthorized,
)
from app.domain.common.enums import EntityType

logger = logging.getLogger(__name__)


def _error(
    status: int,
    code: ResponseCode,
    details: object | None = None,
    data: object | None = None,
    entity_type: EntityType | None = None,
) -> JSONResponse:
    body = ApiResponse[object](
        code=code,
        entity_type=entity_type,
        status=format_http_status(status),
        data=data,
        details=details,
    )
    return JSONResponse(status_code=status, content=jsonable_encoder(body))


async def handle_http_exception(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    http_exception = cast(StarletteHTTPException, exception)
    code = {
        401: ResponseCode.UNAUTHORIZED,
        403: ResponseCode.FORBIDDEN,
        404: ResponseCode.NOT_FOUND,
        409: ResponseCode.CONFLICT,
        422: ResponseCode.VALIDATION_ERROR,
    }.get(http_exception.status_code, ResponseCode.HTTP_ERROR)
    return _error(http_exception.status_code, code, http_exception.detail)


async def handle_validation_exception(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    validation_error = cast(RequestValidationError, exception)
    error_fields = {"loc", "type", "msg"}
    errors = [
        {key: value for key, value in error.items() if key in error_fields}
        for error in validation_error.errors()
    ]
    return _error(422, ResponseCode.VALIDATION_ERROR, data=errors)


async def handle_unexpected_exception(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled application error request_id=%s",
        getattr(request.state, "request_id", None),
    )
    return _error(500, ResponseCode.INTERNAL_ERROR)


async def handle_not_found(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    return _error(
        404,
        ResponseCode.NOT_FOUND,
        str(exception),
        entity_type=_entity_type(exception),
    )


async def handle_invalid_input(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    return _error(
        422,
        ResponseCode.INVALID_INPUT,
        str(exception),
        entity_type=_entity_type(exception),
    )


async def handle_conflict(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    return _error(
        409,
        ResponseCode.CONFLICT,
        str(exception),
        entity_type=_entity_type(exception),
    )


def _entity_type(exception: Exception) -> EntityType | None:
    exception_name = type(exception).__name__.lower()
    matches = [
        entity_type
        for entity_type in EntityType
        if entity_type.name.lower().replace("_", "") in exception_name
    ]
    return max(matches, key=lambda item: len(item.name), default=None)


async def handle_unauthorized(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    response = _error(401, ResponseCode.UNAUTHORIZED, str(exception))
    response.headers["WWW-Authenticate"] = "Bearer"
    return response


async def handle_change_log_cursor_expired(
    _request: Request,
    exception: Exception,
) -> JSONResponse:
    cursor_error = cast(ChangeLogCursorExpired, exception)
    return _error(
        status.HTTP_410_GONE,
        ResponseCode.RESYNC_REQUIRED,
        str(cursor_error),
        ChangeLogResyncRequired(
            restart_sequence=cursor_error.restart_sequence
        ).model_dump(),
        EntityType.CHANGE_LOG,
    )


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
    application.add_exception_handler(
        ChangeLogCursorExpired,
        handle_change_log_cursor_expired,
    )
