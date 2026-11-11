from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.device_group import (
    CreateDeviceGroup,
    DeleteDeviceGroup,
    GetDeviceGroup,
    GetUserDeviceGroups,
    UpdateDeviceGroup,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.infrastructure.device_groups import (
    provide_create_device_group,
    provide_delete_device_group,
    provide_get_device_group,
    provide_get_user_device_groups,
    provide_update_device_group,
)


def get_create_device_group_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateDeviceGroup:
    return provide_create_device_group(session)


def get_get_device_group_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetDeviceGroup:
    return provide_get_device_group(session)


def get_get_user_device_groups_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetUserDeviceGroups:
    return provide_get_user_device_groups(session)


def get_update_device_group_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateDeviceGroup:
    return provide_update_device_group(session)


def get_delete_device_group_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> DeleteDeviceGroup:
    return provide_delete_device_group(session)
