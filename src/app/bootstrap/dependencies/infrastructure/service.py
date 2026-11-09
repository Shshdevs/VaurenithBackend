from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.service import (
    CreateService,
    DeleteService,
    GetDeviceServices,
    GetEnvironmentServices,
    GetProjectServices,
    GetService,
    GetUserServices,
    UpdateService,
    UpdateServiceStatus,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.infrastructure.services import (
    provide_create_service,
    provide_delete_service,
    provide_get_device_services,
    provide_get_environment_services,
    provide_get_project_services,
    provide_get_service,
    provide_get_user_services,
    provide_update_service,
    provide_update_service_status,
)


def get_create_service_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateService:
    return provide_create_service(session)


def get_get_service_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetService:
    return provide_get_service(session)


def get_get_user_services_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetUserServices:
    return provide_get_user_services(session)


def get_get_device_services_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetDeviceServices:
    return provide_get_device_services(session)


def get_get_project_services_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetProjectServices:
    return provide_get_project_services(session)


def get_get_environment_services_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetEnvironmentServices:
    return provide_get_environment_services(session)


def get_update_service_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateService:
    return provide_update_service(session)


def get_update_service_status_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateServiceStatus:
    return provide_update_service_status(session)


def get_delete_service_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> DeleteService:
    return provide_delete_service(session)
