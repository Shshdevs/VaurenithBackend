from collections.abc import Awaitable, Callable

from fastapi import APIRouter

from ....application.health.use_cases.check_database_health import (
    CheckDatabaseHealth,
)
from ....application.identity.dto.verified_identity import VerifiedIdentity
from ....application.identity.use_cases.create_user import CreateUser
from ....application.identity.use_cases.get_current_user import GetCurrentUser
from .health import build_health_router
from .user import build_user_router


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
    return router
