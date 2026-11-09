from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.device_group import (
    CreateDeviceGroup,
    DeleteDeviceGroup,
    GetDeviceGroup,
    UpdateDeviceGroup,
)
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyDeviceGroupRepository,
)


def provide_create_device_group(session: AsyncSession) -> CreateDeviceGroup:
    return CreateDeviceGroup(SqlAlchemyDeviceGroupRepository(session))


def provide_get_device_group(session: AsyncSession) -> GetDeviceGroup:
    return GetDeviceGroup(SqlAlchemyDeviceGroupRepository(session))


def provide_update_device_group(session: AsyncSession) -> UpdateDeviceGroup:
    return UpdateDeviceGroup(SqlAlchemyDeviceGroupRepository(session))


def provide_delete_device_group(session: AsyncSession) -> DeleteDeviceGroup:
    return DeleteDeviceGroup(SqlAlchemyDeviceGroupRepository(session))
