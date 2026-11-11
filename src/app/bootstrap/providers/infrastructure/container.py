from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.container import (
    CreateContainer,
    DeleteContainer,
    GetContainer,
    GetContainersByProject,
    GetDeviceContainers,
    GetEnvironmentContainers,
    GetServiceContainers,
    GetUserContainers,
    UpdateContainer,
)
from app.application.synchronization.use_cases.change_log import RecordChange
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyContainerRepository,
)
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_container(session: AsyncSession) -> CreateContainer:
    return CreateContainer(
        SqlAlchemyContainerRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_container(session: AsyncSession) -> GetContainer:
    return GetContainer(SqlAlchemyContainerRepository(session))


def provide_get_user_containers(session: AsyncSession) -> GetUserContainers:
    return GetUserContainers(SqlAlchemyContainerRepository(session))


def provide_get_device_containers(session: AsyncSession) -> GetDeviceContainers:
    return GetDeviceContainers(SqlAlchemyContainerRepository(session))


def provide_get_project_containers(session: AsyncSession) -> GetContainersByProject:
    return GetContainersByProject(SqlAlchemyContainerRepository(session))


def provide_get_environment_containers(session: AsyncSession) -> GetEnvironmentContainers:
    return GetEnvironmentContainers(SqlAlchemyContainerRepository(session))


def provide_get_service_containers(session: AsyncSession) -> GetServiceContainers:
    return GetServiceContainers(SqlAlchemyContainerRepository(session))


def provide_update_container(session: AsyncSession) -> UpdateContainer:
    return UpdateContainer(
        SqlAlchemyContainerRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_delete_container(session: AsyncSession) -> DeleteContainer:
    return DeleteContainer(
        SqlAlchemyContainerRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )
