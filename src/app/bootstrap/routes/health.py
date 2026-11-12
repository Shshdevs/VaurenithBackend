from fastapi import APIRouter

from app.api.routes.v1.health import build_health_entity_router
from app.api.routes.v1.health.health import build_health_router as build_health_check_router
from app.bootstrap.dependencies.health import get_database_health_check


def build_health_api_router() -> APIRouter:
    router = APIRouter()
    entity_router = build_health_check_router(get_database_health_check)
    router.include_router(build_health_entity_router([entity_router]))
    return router
