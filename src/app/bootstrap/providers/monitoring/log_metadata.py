from sqlalchemy.ext.asyncio import AsyncSession

from app.application.monitoring import CreateLogMetadata, GetUserLogMetadata
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyContainerRepository,
    SqlAlchemyDeviceRepository,
    SqlAlchemyServiceRepository,
)
from app.infrastructure.persistence.repositories.monitoring import (
    SqlAlchemyLogMetadataRepository,
)
from app.infrastructure.persistence.repositories.projects import (
    SqlAlchemyProjectRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_log_metadata(session: AsyncSession) -> CreateLogMetadata:
    return CreateLogMetadata(
        SqlAlchemyLogMetadataRepository(session),
        SqlAlchemyProjectRepository(session),
        SqlAlchemyDeviceRepository(session),
        SqlAlchemyServiceRepository(session),
        SqlAlchemyContainerRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_user_log_metadata(session: AsyncSession) -> GetUserLogMetadata:
    return GetUserLogMetadata(SqlAlchemyLogMetadataRepository(session))
