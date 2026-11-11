from sqlalchemy.ext.asyncio import AsyncSession

from app.application.development import (
    CreateCodeComponent,
    DeleteCodeComponent,
    GetCodeComponent,
    GetRepositoryCodeComponents,
    UpdateCodeComponent,
)
from app.application.synchronization.use_cases.change_log import RecordChange
from app.infrastructure.persistence.repositories.development import (
    SqlAlchemyCodeComponentRepository,
    SqlAlchemyRepositoryRepository,
)
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_code_component(session: AsyncSession) -> CreateCodeComponent:
    return CreateCodeComponent(
        SqlAlchemyCodeComponentRepository(session),
        SqlAlchemyRepositoryRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_code_component(session: AsyncSession) -> GetCodeComponent:
    return GetCodeComponent(SqlAlchemyCodeComponentRepository(session))


def provide_get_repository_code_components(
    session: AsyncSession,
) -> GetRepositoryCodeComponents:
    return GetRepositoryCodeComponents(
        SqlAlchemyCodeComponentRepository(session),
        SqlAlchemyRepositoryRepository(session),
    )


def provide_update_code_component(session: AsyncSession) -> UpdateCodeComponent:
    return UpdateCodeComponent(
        SqlAlchemyCodeComponentRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_delete_code_component(session: AsyncSession) -> DeleteCodeComponent:
    return DeleteCodeComponent(
        SqlAlchemyCodeComponentRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )
