from fastapi import APIRouter

from app.api.routes.v1.infrastructure.device_group import build_device_group_router
from app.bootstrap.dependencies.identity import get_authenticated_identity
from app.bootstrap.dependencies.infrastructure.device_group import (
    get_create_device_group_dependency,
    get_delete_device_group_dependency,
    get_get_device_group_dependency,
    get_update_device_group_dependency,
)


def build_infrastructure_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(
        build_device_group_router(
            create_device_group_dependency=get_create_device_group_dependency,
            get_device_group_dependency=get_get_device_group_dependency,
            update_device_group_dependency=get_update_device_group_dependency,
            delete_device_group_dependency=get_delete_device_group_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        )
    )

    return router
