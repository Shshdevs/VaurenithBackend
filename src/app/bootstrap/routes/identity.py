from fastapi import APIRouter

from app.api.routes.v1.identity import build_identity_entity_router
from app.api.routes.v1.identity.client_device import build_client_device_router
from app.api.routes.v1.identity.user import build_user_router
from app.bootstrap.dependencies.identity import (
    get_authenticated_identity,
    get_client_device,
    get_create_device_session,
    get_create_user,
    get_current_user,
    get_delete_user,
    get_list_client_devices,
    get_list_device_sessions,
    get_register_client_device,
    get_revoke_client_device,
    get_revoke_session,
    get_set_client_device_status,
    get_update_client_device,
    get_verified_identity,
)


def build_identity_api_router() -> APIRouter:
    entity_router = build_user_router(
        get_current_user_dependency=get_current_user,
        delete_user_dependency=get_delete_user,
        create_user_dependency=get_create_user,
        revoke_session_dependency=get_revoke_session,
        authenticated_identity_dependency=get_authenticated_identity,
        verified_identity_dependency=get_verified_identity,
    )
    router = APIRouter()
    client_device_router = build_client_device_router(
        register_client_device_dependency=get_register_client_device,
        list_client_devices_dependency=get_list_client_devices,
        get_client_device_dependency=get_client_device,
        update_client_device_dependency=get_update_client_device,
        create_device_session_dependency=get_create_device_session,
        list_device_sessions_dependency=get_list_device_sessions,
        set_client_device_status_dependency=get_set_client_device_status,
        revoke_client_device_dependency=get_revoke_client_device,
        authenticated_identity_dependency=get_authenticated_identity,
        verified_identity_dependency=get_verified_identity,
    )
    router.include_router(
        build_identity_entity_router([entity_router, client_device_router])
    )
    return router
