from fastapi import APIRouter

from app.api.routes.v1.router import build_router
from app.bootstrap.routes.health import build_health_api_router
from app.bootstrap.routes.identity import build_identity_api_router
from app.bootstrap.routes.projects import build_projects_api_router


def build_api_router(prefix: str) -> APIRouter:
    return build_router(
        prefix=prefix,
        health_router=build_health_api_router(),
        identity_router=build_identity_api_router(),
        projects_router=build_projects_api_router(),
    )
