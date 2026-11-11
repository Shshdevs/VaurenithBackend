from sqlalchemy.ext.asyncio import AsyncSession

from app.application.development import (
    CreateRepository,
    DeleteRepository,
    GetProjectRepositories,
    GetRepository,
    GetUserRepositories,
    UpdateRepository,
)
from app.application.synchronization.use_cases.change_log import RecordChange
from app.infrastructure.persistence.repositories.development import (
    SqlAlchemyRepositoryRepository,
)
from app.infrastructure.persistence.repositories.projects import (
    SqlAlchemyProjectRepository,
)
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_repository(session: AsyncSession) -> CreateRepository:
    return CreateRepository(
        SqlAlchemyRepositoryRepository(session),
        SqlAlchemyProjectRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_repository(session: AsyncSession) -> GetRepository:
    return GetRepository(SqlAlchemyRepositoryRepository(session))


def provide_get_user_repositories(session: AsyncSession) -> GetUserRepositories:
    return GetUserRepositories(SqlAlchemyRepositoryRepository(session))


def provide_get_project_repositories(session: AsyncSession) -> GetProjectRepositories:
    return GetProjectRepositories(
        SqlAlchemyRepositoryRepository(session),
        SqlAlchemyProjectRepository(session),
    )


def provide_update_repository(session: AsyncSession) -> UpdateRepository:
    return UpdateRepository(
        SqlAlchemyRepositoryRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_delete_repository(session: AsyncSession) -> DeleteRepository:
    return DeleteRepository(
        SqlAlchemyRepositoryRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )
