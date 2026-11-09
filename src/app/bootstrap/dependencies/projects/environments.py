from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.projects.use_cases.environments import (
    CreateEnvironment,
    DeleteEnvironment,
    GetEnvironment,
    GetProjectEnvironments,
    UpdateEnvironment,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.projects import (
    provide_create_environment,
    provide_delete_environment,
    provide_get_environment,
    provide_get_project_environments,
    provide_update_environment,
)


def get_create_environment_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> CreateEnvironment:
    return provide_create_environment(session)


def get_get_environment_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetEnvironment:
    return provide_get_environment(session)


def get_get_project_environments_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetProjectEnvironments:
    return provide_get_project_environments(session)


def get_update_environment_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> UpdateEnvironment:
    return provide_update_environment(session)


def get_delete_environment_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> DeleteEnvironment:
    return provide_delete_environment(session)


__all__ = [
    "get_create_environment_dependency",
    "get_get_environment_dependency",
    "get_get_project_environments_dependency",
    "get_update_environment_dependency",
    "get_delete_environment_dependency",
]
