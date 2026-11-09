from sqlalchemy.ext.asyncio import AsyncSession

from app.application.projects.use_cases.environments import (
    CreateEnvironment,
    DeleteEnvironment,
    GetEnvironment,
    GetProjectEnvironments,
    UpdateEnvironment,
)
from app.infrastructure.persistence.repositories.projects import (
    SqlAlchemyEnvironmentRepository,
)


def provide_create_environment(session: AsyncSession) -> CreateEnvironment:
    return CreateEnvironment(SqlAlchemyEnvironmentRepository(session))


def provide_get_environment(session: AsyncSession) -> GetEnvironment:
    return GetEnvironment(SqlAlchemyEnvironmentRepository(session))


def provide_get_project_environments(session: AsyncSession) -> GetProjectEnvironments:
    return GetProjectEnvironments(SqlAlchemyEnvironmentRepository(session))


def provide_update_environment(session: AsyncSession) -> UpdateEnvironment:
    return UpdateEnvironment(SqlAlchemyEnvironmentRepository(session))


def provide_delete_environment(session: AsyncSession) -> DeleteEnvironment:
    return DeleteEnvironment(SqlAlchemyEnvironmentRepository(session))


__all__ = [
    "provide_create_environment",
    "provide_get_environment",
    "provide_get_project_environments",
    "provide_update_environment",
    "provide_delete_environment",
]
