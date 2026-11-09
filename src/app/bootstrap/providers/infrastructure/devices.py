from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.device import (
    CreateDevice,
    DeleteDevice,
    GetDevice,
    GetUserDevices,
    UpdateDevice,
)
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyDeviceRepository,
)


def provide_create_device(session: AsyncSession) -> CreateDevice:
    return CreateDevice(SqlAlchemyDeviceRepository(session))


def provide_get_device(session: AsyncSession) -> GetDevice:
    return GetDevice(SqlAlchemyDeviceRepository(session))


def provide_get_user_devices(session: AsyncSession) -> GetUserDevices:
    return GetUserDevices(SqlAlchemyDeviceRepository(session))


def provide_update_device(session: AsyncSession) -> UpdateDevice:
    return UpdateDevice(SqlAlchemyDeviceRepository(session))


def provide_delete_device(session: AsyncSession) -> DeleteDevice:
    return DeleteDevice(SqlAlchemyDeviceRepository(session))
