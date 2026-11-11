from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.database import (
    CreateDatabase,
    DeleteDatabase,
    GetDatabase,
    GetDatabasesByContainer,
    GetDatabasesByDevice,
    GetDatabasesByEnvironment,
    GetDatabasesByProject,
    GetDatabasesByService,
    GetUserDatabases,
    UpdateDatabase,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.infrastructure.databases import (
    provide_create_database,
    provide_delete_database,
    provide_get_container_databases,
    provide_get_database,
    provide_get_device_databases,
    provide_get_environment_databases,
    provide_get_project_databases,
    provide_get_service_databases,
    provide_get_user_databases,
    provide_update_database,
)


def get_create_database_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateDatabase:
    return provide_create_database(session)


def get_get_database_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetDatabase:
    return provide_get_database(session)


def get_get_user_databases_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetUserDatabases:
    return provide_get_user_databases(session)


def get_get_device_databases_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetDatabasesByDevice:
    return provide_get_device_databases(session)


def get_get_project_databases_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetDatabasesByProject:
    return provide_get_project_databases(session)


def get_get_environment_databases_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetDatabasesByEnvironment:
    return provide_get_environment_databases(session)


def get_get_container_databases_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetDatabasesByContainer:
    return provide_get_container_databases(session)


def get_get_service_databases_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetDatabasesByService:
    return provide_get_service_databases(session)


def get_update_database_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateDatabase:
    return provide_update_database(session)


def get_delete_database_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> DeleteDatabase:
    return provide_delete_database(session)
