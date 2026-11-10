from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.service import (
    CreateService,
    DeleteService,
    GetDeviceServices,
    GetEnvironmentServices,
    GetProjectServices,
    GetService,
    GetUserServices,
    UpdateService,
    UpdateServiceStatus,
)
from app.application.synchronization import RecordChange
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyServiceRepository,
)
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)


def provide_create_service(session: AsyncSession) -> CreateService:
    return CreateService(
        SqlAlchemyServiceRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
    )


def provide_get_service(session: AsyncSession) -> GetService:
    return GetService(SqlAlchemyServiceRepository(session))


def provide_get_user_services(session: AsyncSession) -> GetUserServices:
    return GetUserServices(SqlAlchemyServiceRepository(session))


def provide_get_device_services(session: AsyncSession) -> GetDeviceServices:
    return GetDeviceServices(SqlAlchemyServiceRepository(session))


def provide_get_project_services(session: AsyncSession) -> GetProjectServices:
    return GetProjectServices(SqlAlchemyServiceRepository(session))


def provide_get_environment_services(session: AsyncSession) -> GetEnvironmentServices:
    return GetEnvironmentServices(SqlAlchemyServiceRepository(session))


def provide_update_service(session: AsyncSession) -> UpdateService:
    return UpdateService(
        SqlAlchemyServiceRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
    )


def provide_update_service_status(session: AsyncSession) -> UpdateServiceStatus:
    return UpdateServiceStatus(
        SqlAlchemyServiceRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
    )


def provide_delete_service(session: AsyncSession) -> DeleteService:
    return DeleteService(
        SqlAlchemyServiceRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
    )
