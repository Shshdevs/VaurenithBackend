from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.development import (
    CreateRepository,
    DeleteRepository,
    GetProjectRepositories,
    GetRepository,
    GetUserRepositories,
    UpdateRepository,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.development import (
    provide_create_repository,
    provide_delete_repository,
    provide_get_project_repositories,
    provide_get_repository,
    provide_get_user_repositories,
    provide_update_repository,
)


def create_repository_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateRepository:
    return provide_create_repository(session)


def get_repository_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetRepository:
    return provide_get_repository(session)


def get_user_repositories_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetUserRepositories:
    return provide_get_user_repositories(session)


def get_project_repositories_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetProjectRepositories:
    return provide_get_project_repositories(session)


def update_repository_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateRepository:
    return provide_update_repository(session)


def delete_repository_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> DeleteRepository:
    return provide_delete_repository(session)
