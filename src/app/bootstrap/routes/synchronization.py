from fastapi import APIRouter

from app.api.routes.v1.synchronization.change_log import build_change_log_route
from app.bootstrap.dependencies.identity import get_authenticated_identity
from app.bootstrap.dependencies.synchronization import get_user_change_log_dependency


def build_synchronization_api_router() -> APIRouter:
    return build_change_log_route(
        get_user_change_log_dependency=get_user_change_log_dependency,
        authenticated_identity_dependency=get_authenticated_identity,
    )
