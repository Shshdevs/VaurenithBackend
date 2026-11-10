from sqlalchemy.ext.asyncio import AsyncSession

from app.application.projects.use_cases.projects import (
    CreateProject,
    DeleteProject,
    GetProject,
    GetUserProjects,
    UpdateProject,
)
from app.application.synchronization import RecordChange
from app.infrastructure.persistence.repositories.projects import SqlAlchemyProjectRepository
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)


def provide_create_project(session: AsyncSession) -> CreateProject:
    return CreateProject(
        SqlAlchemyProjectRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
    )


def provide_get_project(session: AsyncSession) -> GetProject:
    return GetProject(SqlAlchemyProjectRepository(session))


def provide_get_user_projects(session: AsyncSession) -> GetUserProjects:
    return GetUserProjects(SqlAlchemyProjectRepository(session))


def provide_update_project(session: AsyncSession) -> UpdateProject:
    return UpdateProject(
        SqlAlchemyProjectRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
    )


def provide_delete_project(session: AsyncSession) -> DeleteProject:
    return DeleteProject(
        SqlAlchemyProjectRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
    )


__all__ = [
    "provide_create_project",
    "provide_get_project",
    "provide_get_user_projects",
    "provide_update_project",
    "provide_delete_project",
]
