from fastapi import APIRouter

from app.bootstrap.routes.automation import build_automation_api_router
from app.bootstrap.routes.development import build_development_api_router
from app.bootstrap.routes.health import build_health_api_router
from app.bootstrap.routes.identity import build_identity_api_router
from app.bootstrap.routes.infrastructure import build_infrastructure_api_router
from app.bootstrap.routes.monitoring import build_monitoring_api_router
from app.bootstrap.routes.preferences import build_preferences_api_router
from app.bootstrap.routes.projects import build_projects_api_router
from app.bootstrap.routes.synchronization import build_synchronization_api_router


def build_api_router(prefix: str) -> APIRouter:
    router = APIRouter()
    router.include_router(build_health_api_router(), prefix=prefix)
    router.include_router(build_identity_api_router(), prefix=prefix)
    router.include_router(build_projects_api_router(), prefix=prefix)
    router.include_router(build_infrastructure_api_router(), prefix=prefix)
    router.include_router(build_synchronization_api_router(), prefix=prefix)
    router.include_router(build_preferences_api_router(), prefix=prefix)
    router.include_router(build_monitoring_api_router(), prefix=prefix)
    router.include_router(build_development_api_router(), prefix=prefix)
    router.include_router(build_automation_api_router(), prefix=prefix)
    return router
