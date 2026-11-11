from fastapi import APIRouter

from app.api.routes.v1.router import build_router
from app.bootstrap.routes.health import build_health_api_router
from app.bootstrap.routes.identity import build_identity_api_router
from app.bootstrap.routes.infrastructure import build_infrastructure_api_router
from app.bootstrap.routes.monitoring import build_monitoring_api_router
from app.bootstrap.routes.preferences import build_preferences_api_router
from app.bootstrap.routes.projects import build_projects_api_router
from app.bootstrap.routes.synchronization import build_synchronization_api_router


def build_api_router(prefix: str) -> APIRouter:
    return build_router(
        prefix=prefix,
        health_router=build_health_api_router(),
        identity_router=build_identity_api_router(),
        projects_router=build_projects_api_router(),
        infrastructure_router=build_infrastructure_api_router(),
        synchronization_router=build_synchronization_api_router(),
        preferences_router=build_preferences_api_router(),
        monitoring_router=build_monitoring_api_router(),
    )
