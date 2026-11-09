from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.device_group import (
    CreateDeviceGroup,
    DeleteDeviceGroup,
    GetDeviceGroup,
    UpdateDeviceGroup,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.infrastructure.device_groups import (
    provide_create_device_group,
    provide_delete_device_group,
    provide_get_device_group,
    provide_update_device_group,
)


def get_create_device_group_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> CreateDeviceGroup:
    return provide_create_device_group(session)


def get_get_device_group_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> GetDeviceGroup:
    return provide_get_device_group(session)


def get_update_device_group_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> UpdateDeviceGroup:
    return provide_update_device_group(session)


def get_delete_device_group_dependency(
    session: AsyncSession = Depends(get_database_session),
) -> DeleteDeviceGroup:
    return provide_delete_device_group(session)
