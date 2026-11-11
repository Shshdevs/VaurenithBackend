from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.container import (
    CreateContainer,
    DeleteContainer,
    GetContainer,
    GetContainersByProject,
    GetDeviceContainers,
    GetEnvironmentContainers,
    GetServiceContainers,
    GetUserContainers,
    UpdateContainer,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.infrastructure.container import (
    provide_create_container,
    provide_delete_container,
    provide_get_container,
    provide_get_device_containers,
    provide_get_environment_containers,
    provide_get_project_containers,
    provide_get_service_containers,
    provide_get_user_containers,
    provide_update_container,
)


def get_create_container_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateContainer:
    return provide_create_container(session)


def get_get_container_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetContainer:
    return provide_get_container(session)


def get_get_user_containers_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetUserContainers:
    return provide_get_user_containers(session)


def get_get_device_containers_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetDeviceContainers:
    return provide_get_device_containers(session)


def get_get_service_containers_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetServiceContainers:
    return provide_get_service_containers(session)


def get_get_project_containers_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetContainersByProject:
    return provide_get_project_containers(session)


def get_get_environment_containers_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetEnvironmentContainers:
    return provide_get_environment_containers(session)


def get_update_container_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateContainer:
    return provide_update_container(session)


def get_delete_container_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> DeleteContainer:
    return provide_delete_container(session)
