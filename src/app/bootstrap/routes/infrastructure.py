from fastapi import APIRouter

from app.api.routes.v1.infrastructure import build_infrastructure_entity_router
from app.api.routes.v1.infrastructure.connection import build_connection_router
from app.api.routes.v1.infrastructure.container import build_container_router
from app.api.routes.v1.infrastructure.database import build_database_router
from app.api.routes.v1.infrastructure.device import build_device_router
from app.api.routes.v1.infrastructure.device_group import build_device_group_router
from app.api.routes.v1.infrastructure.service import build_service_router
from app.bootstrap.dependencies.identity import get_authenticated_identity
from app.bootstrap.dependencies.infrastructure.connection import (
    get_create_connection_dependency,
    get_delete_connection_dependency,
    get_get_connection_dependency,
    get_get_device_connections_dependency,
    get_get_user_connections_dependency,
    get_report_connection_status_dependency,
    get_update_connection_dependency,
)
from app.bootstrap.dependencies.infrastructure.container import (
    get_create_container_dependency,
    get_delete_container_dependency,
    get_get_container_dependency,
    get_get_device_containers_dependency,
    get_get_environment_containers_dependency,
    get_get_project_containers_dependency,
    get_get_service_containers_dependency,
    get_get_user_containers_dependency,
    get_update_container_dependency,
)
from app.bootstrap.dependencies.infrastructure.database import (
    get_create_database_dependency,
    get_delete_database_dependency,
    get_get_container_databases_dependency,
    get_get_database_dependency,
    get_get_device_databases_dependency,
    get_get_environment_databases_dependency,
    get_get_project_databases_dependency,
    get_get_service_databases_dependency,
    get_get_user_databases_dependency,
    get_update_database_dependency,
)
from app.bootstrap.dependencies.infrastructure.device import (
    get_create_device_dependency,
    get_delete_device_dependency,
    get_get_device_dependency,
    get_get_user_devices_dependency,
    get_update_device_dependency,
)
from app.bootstrap.dependencies.infrastructure.device_group import (
    add_device_group_member_dependency,
    get_create_device_group_dependency,
    get_delete_device_group_dependency,
    get_device_group_members_dependency,
    get_get_device_group_dependency,
    get_get_user_device_groups_dependency,
    get_update_device_group_dependency,
    remove_device_group_member_dependency,
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
    entity_routers = []
    entity_routers.append(
        build_connection_router(
            create_connection_dependency=get_create_connection_dependency,
            get_connection_dependency=get_get_connection_dependency,
            get_user_connections_dependency=get_get_user_connections_dependency,
            get_device_connections_dependency=get_get_device_connections_dependency,
            update_connection_dependency=get_update_connection_dependency,
            report_connection_status_dependency=get_report_connection_status_dependency,
            delete_connection_dependency=get_delete_connection_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        )
    )
    entity_routers.append(
        build_device_router(
            create_device_dependency=get_create_device_dependency,
            get_device_dependency=get_get_device_dependency,
            get_user_devices_dependency=get_get_user_devices_dependency,
            update_device_dependency=get_update_device_dependency,
            delete_device_dependency=get_delete_device_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        )
    )
    entity_routers.append(
        build_device_group_router(
            create_device_group_dependency=get_create_device_group_dependency,
            get_device_group_dependency=get_get_device_group_dependency,
            get_user_device_groups_dependency=get_get_user_device_groups_dependency,
            get_device_group_members_dependency=get_device_group_members_dependency,
            add_device_group_member_dependency=add_device_group_member_dependency,
            remove_device_group_member_dependency=remove_device_group_member_dependency,
            update_device_group_dependency=get_update_device_group_dependency,
            delete_device_group_dependency=get_delete_device_group_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        )
    )
    entity_routers.append(
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
    entity_routers.append(
        build_container_router(
            create_container_dependency=get_create_container_dependency,
            get_container_dependency=get_get_container_dependency,
            get_user_containers_dependency=get_get_user_containers_dependency,
            get_device_containers_dependency=get_get_device_containers_dependency,
            get_project_containers_dependency=get_get_project_containers_dependency,
            get_environment_containers_dependency=get_get_environment_containers_dependency,
            get_service_containers_dependency=get_get_service_containers_dependency,
            update_container_dependency=get_update_container_dependency,
            delete_container_dependency=get_delete_container_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        )
    )
    entity_routers.append(
        build_database_router(
            create_database_dependency=get_create_database_dependency,
            get_database_dependency=get_get_database_dependency,
            get_user_databases_dependency=get_get_user_databases_dependency,
            get_device_databases_dependency=get_get_device_databases_dependency,
            get_project_databases_dependency=get_get_project_databases_dependency,
            get_environment_databases_dependency=get_get_environment_databases_dependency,
            get_container_databases_dependency=get_get_container_databases_dependency,
            get_service_databases_dependency=get_get_service_databases_dependency,
            update_database_dependency=get_update_database_dependency,
            delete_database_dependency=get_delete_database_dependency,
            authenticated_identity_dependency=get_authenticated_identity,
        )
    )

    router = APIRouter()
    router.include_router(build_infrastructure_entity_router(entity_routers))
    return router
