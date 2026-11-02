import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..schemas.response import ApiResponse

logger = logging.getLogger(__name__)


def _error(status: int, message: str, data: object | None = None) -> JSONResponse:
    body = ApiResponse[object](message=message, data=data)
    return JSONResponse(status_code=status, content=jsonable_encoder(body))


def register_error_handlers(application: FastAPI) -> None:
    @application.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        _request: Request, exception: StarletteHTTPException
    ) -> JSONResponse:
        message = (
            exception.detail if isinstance(exception.detail, str) else "HTTP error"
        )
        return _error(exception.status_code, message)

    @application.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        _request: Request, exception: RequestValidationError
    ) -> JSONResponse:
        return _error(422, "Request validation failed", exception.errors())

    @application.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request, exception: Exception
    ) -> JSONResponse:
        logger.exception(
            "Unhandled application error request_id=%s",
            getattr(request.state, "request_id", None),
        )
        return _error(500, "Internal server error")
