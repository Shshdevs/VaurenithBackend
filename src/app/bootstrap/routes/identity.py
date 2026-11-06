from fastapi import APIRouter

from app.api.routes.v1.identity.user import build_user_router
from app.bootstrap.dependencies.identity import (
    get_authenticated_identity,
    get_create_user,
    get_current_user,
    get_verified_identity,
)


def build_identity_api_router() -> APIRouter:
    return build_user_router(
        get_current_user_dependency=get_current_user,
        create_user_dependency=get_create_user,
        authenticated_identity_dependency=get_authenticated_identity,
        verified_identity_dependency=get_verified_identity,
    )
