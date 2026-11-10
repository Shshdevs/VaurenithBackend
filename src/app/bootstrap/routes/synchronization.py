from fastapi import APIRouter

from app.api.routes.v1.synchronization.change_log import build_change_log_route
from app.api.routes.v1.synchronization.sync_state import build_sync_state_route
from app.bootstrap.dependencies.identity import get_authenticated_identity
from app.bootstrap.dependencies.synchronization import (
    create_sync_state_dependency,
    delete_sync_state_dependency,
    get_sync_state_dependency,
    get_user_change_log_dependency,
    update_sync_state_dependency,
    update_sync_status_dependency,
)


def build_synchronization_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(
        build_change_log_route(
            get_user_change_log_dependency=get_user_change_log_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        )
    )

    router.include_router(
        build_sync_state_route(
            get_delete_sync_state_dependency=delete_sync_state_dependency,
            get_update_sync_status_dependency=update_sync_status_dependency,
            get_update_sync_state_dependency=update_sync_state_dependency,
            get_get_sync_state_dependency=get_sync_state_dependency,
            get_create_sync_state_dependency=create_sync_state_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        )
    )
    return router
