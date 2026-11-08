from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.projects.use_cases.projects import (
    CreateProject,
    DeleteProject,
    GetProject,
    GetUserProjects,
    UpdateProject,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers import (
    provide_create_project,
    provide_delete_project,
    provide_get_project,
    provide_get_user_projects,
    provide_update_project,
)


def get_create_project_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> CreateProject:
    return provide_create_project(session)


def get_get_project_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetProject:
    return provide_get_project(session)


def get_get_user_projects_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetUserProjects:
    return provide_get_user_projects(session)


def get_update_project_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> UpdateProject:
    return provide_update_project(session)


def get_delete_project_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> DeleteProject:
    return provide_delete_project(session)
