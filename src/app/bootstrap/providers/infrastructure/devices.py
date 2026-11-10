from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.device import (
    CreateDevice,
    DeleteDevice,
    GetDevice,
    GetUserDevices,
    UpdateDevice,
)
from app.application.synchronization.use_cases.change_log import RecordChange
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyDeviceRepository,
)
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_device(session: AsyncSession) -> CreateDevice:
    return CreateDevice(
        SqlAlchemyDeviceRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_device(session: AsyncSession) -> GetDevice:
    return GetDevice(SqlAlchemyDeviceRepository(session))


def provide_get_user_devices(session: AsyncSession) -> GetUserDevices:
    return GetUserDevices(SqlAlchemyDeviceRepository(session))


def provide_update_device(session: AsyncSession) -> UpdateDevice:
    return UpdateDevice(
        SqlAlchemyDeviceRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_delete_device(session: AsyncSession) -> DeleteDevice:
    return DeleteDevice(
        SqlAlchemyDeviceRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )
