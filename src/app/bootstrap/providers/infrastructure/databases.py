from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.database import (
    CreateDatabase,
    DeleteDatabase,
    GetDatabase,
    GetDatabasesByContainer,
    GetDatabasesByDevice,
    GetDatabasesByEnvironment,
    GetDatabasesByProject,
    GetDatabasesByService,
    GetUserDatabases,
    UpdateDatabase,
)
from app.application.synchronization.use_cases.change_log import RecordChange
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyDatabaseRepository,
)
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_database(session: AsyncSession) -> CreateDatabase:
    return CreateDatabase(
        SqlAlchemyDatabaseRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_database(session: AsyncSession) -> GetDatabase:
    return GetDatabase(SqlAlchemyDatabaseRepository(session))


def provide_get_user_databases(session: AsyncSession) -> GetUserDatabases:
    return GetUserDatabases(SqlAlchemyDatabaseRepository(session))


def provide_get_device_databases(session: AsyncSession) -> GetDatabasesByDevice:
    return GetDatabasesByDevice(SqlAlchemyDatabaseRepository(session))


def provide_get_project_databases(session: AsyncSession) -> GetDatabasesByProject:
    return GetDatabasesByProject(SqlAlchemyDatabaseRepository(session))


def provide_get_environment_databases(
    session: AsyncSession,
) -> GetDatabasesByEnvironment:
    return GetDatabasesByEnvironment(SqlAlchemyDatabaseRepository(session))


def provide_get_container_databases(session: AsyncSession) -> GetDatabasesByContainer:
    return GetDatabasesByContainer(SqlAlchemyDatabaseRepository(session))


def provide_get_service_databases(session: AsyncSession) -> GetDatabasesByService:
    return GetDatabasesByService(SqlAlchemyDatabaseRepository(session))


def provide_update_database(session: AsyncSession) -> UpdateDatabase:
    return UpdateDatabase(
        SqlAlchemyDatabaseRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_delete_database(session: AsyncSession) -> DeleteDatabase:
    return DeleteDatabase(
        SqlAlchemyDatabaseRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )
