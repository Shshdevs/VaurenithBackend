from sqlalchemy.ext.asyncio import AsyncSession

from app.application.projects.use_cases.environments import (
    CreateEnvironment,
    DeleteEnvironment,
    GetEnvironment,
    GetProjectEnvironments,
    UpdateEnvironment,
)
from app.application.projects.use_cases.projects import (
    CreateProject,
    DeleteProject,
    GetProject,
    GetUserProjects,
    UpdateProject,
)
from app.infrastructure.persistence.repositories.projects import (
    SqlAlchemyEnvironmentRepository,
    SqlAlchemyProjectRepository,
)


def provide_create_project(session: AsyncSession) -> CreateProject:
    return CreateProject(SqlAlchemyProjectRepository(session))


def provide_get_project(session: AsyncSession) -> GetProject:
    return GetProject(SqlAlchemyProjectRepository(session))


def provide_get_user_projects(session: AsyncSession) -> GetUserProjects:
    return GetUserProjects(SqlAlchemyProjectRepository(session))


def provide_update_project(session: AsyncSession) -> UpdateProject:
    return UpdateProject(SqlAlchemyProjectRepository(session))


def provide_delete_project(session: AsyncSession) -> DeleteProject:
    return DeleteProject(SqlAlchemyProjectRepository(session))


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
