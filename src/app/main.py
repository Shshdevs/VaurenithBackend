from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.middleware.error_handler import register_error_handlers
from app.api.middleware.request_body_limit import RequestBodyLimitMiddleware
from app.api.middleware.request_context import (
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
)
from app.bootstrap.api import build_api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    application = FastAPI(
        title="Vaurenith API",
        docs_url="/swagger",
        redoc_url="/docs",
    )

    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        RequestBodyLimitMiddleware,
        max_body_size=app_settings.max_request_body_size,
    )
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(build_api_router(prefix=app_settings.api_prefix))
    register_error_handlers(application)

    def openapi_schema():
        if application.openapi_schema is not None:
            return application.openapi_schema
        schema = get_openapi(
            title=application.title,
            version=application.version,
            routes=application.routes,
        )
        schema["x-tagGroups"] = [
            {
                "name": "automation",
                "tags": ["scripts", "script_targets", "script_executions"],
            },
            {
                "name": "development",
                "tags": [
                    "branches",
                    "repositories",
                    "code_components",
                    "commits",
                    "dependencies",
                ],
            },
            {"name": "health", "tags": ["health_checks"]},
            {"name": "identity", "tags": ["users"]},
            {
                "name": "infrastructure",
                "tags": [
                    "connections",
                    "devices",
                    "device_groups",
                    "services",
                    "containers",
                    "databases",
                ],
            },
            {"name": "monitoring", "tags": ["events", "log_metadata", "metrics"]},
            {"name": "preferences", "tags": ["settings"]},
            {"name": "projects", "tags": ["projects", "environments", "project_devices"]},
            {"name": "relations", "tags": ["relations"]},
            {"name": "synchronization", "tags": ["change-log", "sync-state"]},
        ]
        application.openapi_schema = schema
        return schema

    application.openapi = openapi_schema
    return application


app: FastAPI = create_app()
