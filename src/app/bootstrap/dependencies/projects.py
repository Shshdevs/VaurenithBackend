from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.projects.use_cases import CreateProject
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers import provide_create_project


def get_create_project_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> CreateProject:
    return provide_create_project(session)
