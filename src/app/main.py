import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.api.routes.health import router as health_router
from app.api.schemas.response import ApiResponse
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


def _error(status: int, message: str, data: object | None = None) -> JSONResponse:
    body = ApiResponse[object](message=message, data=data)
    return JSONResponse(status_code=status, content=jsonable_encoder(body))


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    application = FastAPI(title="Vaurenith API")

    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health_router, prefix=app_settings.api_prefix)

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

    return application


app: FastAPI = create_app()
