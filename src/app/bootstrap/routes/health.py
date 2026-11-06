from fastapi import APIRouter

from app.api.routes.v1.health.health import build_health_router
from app.bootstrap.dependencies.health import get_database_health_check


def build_health_api_router() -> APIRouter:
    return build_health_router(get_database_health_check)
