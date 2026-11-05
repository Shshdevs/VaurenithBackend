from collections.abc import Callable

from fastapi import APIRouter

from ....application.health.use_cases.check_database_health import (
    CheckDatabaseHealth,
)
from .health import build_health_router


def build_router(
    prefix: str,
    health_check_dependency: Callable[..., CheckDatabaseHealth],
) -> APIRouter:
    router = APIRouter()
    router.include_router(
        build_health_router(health_check_dependency),
        prefix=prefix,
    )
    return router
