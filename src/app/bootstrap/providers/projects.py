from sqlalchemy.ext.asyncio import AsyncSession

from app.application.projects import CreateProject
from app.infrastructure.persistence.repositories.projects import (
    SqlAlchemyProjectRepository,
)


def provide_create_project(session: AsyncSession) -> CreateProject:
    return CreateProject(SqlAlchemyProjectRepository(session))
