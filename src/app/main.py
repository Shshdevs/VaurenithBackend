from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.middleware.error_handler import register_error_handlers
from .api.middleware.request_context import (
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
)
from .api.routes.v1.router import build_router
from .bootstrap.dependencies import (
    get_authenticated_identity,
    get_create_user,
    get_current_user,
    get_database_health_check,
    get_verified_identity,
)
from .core.config import Settings, get_settings
from .core.logging import configure_logging


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
    application.include_router(
        build_router(
            prefix=app_settings.api_prefix,
            health_check_dependency=get_database_health_check,
            get_current_user_dependency=get_current_user,
            create_user_dependency=get_create_user,
            authenticated_identity_dependency=get_authenticated_identity,
            verified_identity_dependency=get_verified_identity,
        )
    )
    register_error_handlers(application)

    return application


app: FastAPI = create_app()
