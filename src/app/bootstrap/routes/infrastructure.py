from fastapi import APIRouter

from app.api.routes.v1.infrastructure.device import build_device_router
from app.api.routes.v1.infrastructure.device_group import build_device_group_router
from app.api.routes.v1.infrastructure.service import build_service_router
from app.bootstrap.dependencies.identity import get_authenticated_identity
from app.bootstrap.dependencies.infrastructure.device import (
    get_create_device_dependency,
    get_delete_device_dependency,
    get_get_device_dependency,
    get_get_user_devices_dependency,
    get_update_device_dependency,
)
from app.bootstrap.dependencies.infrastructure.device_group import (
    get_create_device_group_dependency,
    get_delete_device_group_dependency,
    get_get_device_group_dependency,
    get_update_device_group_dependency,
)
from app.bootstrap.dependencies.infrastructure.service import (
    get_create_service_dependency,
    get_delete_service_dependency,
    get_get_device_services_dependency,
    get_get_environment_services_dependency,
    get_get_project_services_dependency,
    get_get_service_dependency,
    get_get_user_services_dependency,
    get_update_service_dependency,
    get_update_service_status_dependency,
)


def build_infrastructure_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(
        build_device_router(
            create_device_dependency=get_create_device_dependency,
            get_device_dependency=get_get_device_dependency,
            get_user_devices_dependency=get_get_user_devices_dependency,
            update_device_dependency=get_update_device_dependency,
            delete_device_dependency=get_delete_device_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        )
    )
    router.include_router(
        build_device_group_router(
            create_device_group_dependency=get_create_device_group_dependency,
            get_device_group_dependency=get_get_device_group_dependency,
            update_device_group_dependency=get_update_device_group_dependency,
            delete_device_group_dependency=get_delete_device_group_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        )
    )
    router.include_router(
        build_service_router(
            create_service_dependency=get_create_service_dependency,
            get_service_dependency=get_get_service_dependency,
            get_user_services_dependency=get_get_user_services_dependency,
            get_device_services_dependency=get_get_device_services_dependency,
            get_project_services_dependency=get_get_project_services_dependency,
            get_environment_services_dependency=get_get_environment_services_dependency,
            update_service_dependency=get_update_service_dependency,
            update_service_status_dependency=get_update_service_status_dependency,
            delete_service_dependency=get_delete_service_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        )
    )

    return router
