from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.device import (
    CreateDevice,
    DeleteDevice,
    GetDevice,
    GetUserDevices,
    UpdateDevice,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.infrastructure.devices import (
    provide_create_device,
    provide_delete_device,
    provide_get_device,
    provide_get_user_devices,
    provide_update_device,
)


def get_create_device_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> CreateDevice:
    return provide_create_device(session)


def get_get_device_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetDevice:
    return provide_get_device(session)


def get_get_user_devices_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetUserDevices:
    return provide_get_user_devices(session)


def get_update_device_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> UpdateDevice:
    return provide_update_device(session)


def get_delete_device_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> DeleteDevice:
    return provide_delete_device(session)
