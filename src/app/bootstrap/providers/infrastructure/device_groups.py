from sqlalchemy.ext.asyncio import AsyncSession

from app.application.infrastructure.use_cases.device_group import (
    AddDeviceGroupMember,
    CreateDeviceGroup,
    DeleteDeviceGroup,
    GetDeviceGroup,
    GetDeviceGroupMembers,
    GetUserDeviceGroups,
    RemoveDeviceGroupMember,
    UpdateDeviceGroup,
)
from app.application.synchronization.use_cases.change_log import RecordChange
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyDeviceGroupMemberRepository,
    SqlAlchemyDeviceGroupRepository,
    SqlAlchemyDeviceRepository,
)
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_device_group(session: AsyncSession) -> CreateDeviceGroup:
    return CreateDeviceGroup(
        SqlAlchemyDeviceGroupRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_device_group(session: AsyncSession) -> GetDeviceGroup:
    return GetDeviceGroup(SqlAlchemyDeviceGroupRepository(session))


def provide_get_user_device_groups(session: AsyncSession) -> GetUserDeviceGroups:
    return GetUserDeviceGroups(SqlAlchemyDeviceGroupRepository(session))


def provide_get_device_group_members(session: AsyncSession) -> GetDeviceGroupMembers:
    return GetDeviceGroupMembers(
        SqlAlchemyDeviceGroupRepository(session),
        SqlAlchemyDeviceGroupMemberRepository(session),
    )


def provide_add_device_group_member(session: AsyncSession) -> AddDeviceGroupMember:
    return AddDeviceGroupMember(
        SqlAlchemyDeviceGroupRepository(session),
        SqlAlchemyDeviceRepository(session),
        SqlAlchemyDeviceGroupMemberRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_remove_device_group_member(session: AsyncSession) -> RemoveDeviceGroupMember:
    return RemoveDeviceGroupMember(
        SqlAlchemyDeviceGroupRepository(session),
        SqlAlchemyDeviceGroupMemberRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_update_device_group(session: AsyncSession) -> UpdateDeviceGroup:
    return UpdateDeviceGroup(
        SqlAlchemyDeviceGroupRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )


def provide_delete_device_group(session: AsyncSession) -> DeleteDeviceGroup:
    return DeleteDeviceGroup(
        SqlAlchemyDeviceGroupRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
    )
