from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.development import (
    CreateDependency,
    DeleteDependency,
    GetComponentDependencies,
    GetDependency,
    GetRepositoryDependencies,
    UpdateDependency,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.development.dependency import (
    provide_create_dependency,
    provide_delete_dependency,
    provide_get_component_dependencies,
    provide_get_dependency,
    provide_get_repository_dependencies,
    provide_update_dependency,
)


def create_dependency_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateDependency:
    return provide_create_dependency(session)


def get_dependency_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetDependency:
    return provide_get_dependency(session)


def get_component_dependencies_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetComponentDependencies:
    return provide_get_component_dependencies(session)


def get_repository_dependencies_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetRepositoryDependencies:
    return provide_get_repository_dependencies(session)


def update_dependency_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateDependency:
    return provide_update_dependency(session)


def delete_dependency_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> DeleteDependency:
    return provide_delete_dependency(session)
