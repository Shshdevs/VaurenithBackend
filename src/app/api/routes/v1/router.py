from collections.abc import Awaitable, Callable

from fastapi import APIRouter

from app.api.routes.v1.health.health import build_health_router
from app.api.routes.v1.identity.user import build_user_router
from app.api.routes.v1.projects.project import build_project_route
from app.application.health.use_cases import CheckDatabaseHealth
from app.application.identity.dto import VerifiedIdentity
from app.application.identity.use_cases import CreateUser, GetCurrentUser
from app.application.projects.use_cases import CreateProject


def build_router(
    prefix: str,
    health_check_dependency: Callable[..., CheckDatabaseHealth],
    get_current_user_dependency: Callable[..., GetCurrentUser],
    create_user_dependency: Callable[..., CreateUser],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
    verified_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
    get_create_project: Callable[..., CreateProject],
) -> APIRouter:
    router = APIRouter()
    router.include_router(
        build_health_router(health_check_dependency),
        prefix=prefix,
    )
    router.include_router(
        build_user_router(
            get_current_user_dependency,
            create_user_dependency,
            authenticated_identity_dependency,
            verified_identity_dependency,
        ),
        prefix=prefix,
    )
    router.include_router(
        build_project_route(
            create_project_dependency=get_create_project,
            authenticated_identity_dependency=authenticated_identity_dependency,
        ),
        prefix=prefix,
    )
    return router
