from app.infrastructure.persistence.repositories.projects import (
    sqlalchemy_project_repository as _project_repository,
)

SqlAlchemyProjectRepository = _project_repository.SqlAlchemyProjectRepository

__all__ = ["SqlAlchemyProjectRepository"]
