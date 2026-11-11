from uuid import UUID

from sqlalchemy import delete, exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import (
    DeviceGroupMemberAlreadyExists,
    DeviceGroupNotFound,
    DeviceNotFound,
)
from app.application.infrastructure.interfaces import DeviceGroupMemberRepository
from app.domain.infrastructure import DeviceGroupMember as DeviceGroupMemberEntity
from app.infrastructure.persistence.models.infrastructure.device import Device
from app.infrastructure.persistence.models.infrastructure.device_group import DeviceGroup
from app.infrastructure.persistence.models.infrastructure.device_group_member import (
    DeviceGroupMember,
)


class SqlAlchemyDeviceGroupMemberRepository(DeviceGroupMemberRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_group(
        self, identity: VerifiedIdentity, group_id: UUID
    ) -> list[DeviceGroupMemberEntity]:
        result = await self._session.scalars(
            select(DeviceGroupMember)
            .join(DeviceGroup, DeviceGroup.id == DeviceGroupMember.group_id)
            .join(Device, Device.id == DeviceGroupMember.device_id)
            .where(
                DeviceGroup.user_id == identity.user_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
                DeviceGroupMember.group_id == group_id,
            )
            .order_by(DeviceGroupMember.created_at, DeviceGroupMember.id)
        )
        return [self._to_entity(model) for model in result.all()]

    async def get_by_device(
        self, identity: VerifiedIdentity, group_id: UUID, device_id: UUID
    ) -> DeviceGroupMemberEntity | None:
        result = await self._session.scalar(
            select(DeviceGroupMember)
            .join(DeviceGroup, DeviceGroup.id == DeviceGroupMember.group_id)
            .join(Device, Device.id == DeviceGroupMember.device_id)
            .where(
                DeviceGroup.user_id == identity.user_id,
                Device.user_id == identity.user_id,
                DeviceGroupMember.group_id == group_id,
                DeviceGroupMember.device_id == device_id,
            )
        )
        return self._to_entity(result) if result is not None else None

    async def add(
        self, identity: VerifiedIdentity, member: DeviceGroupMemberEntity
    ) -> None:
        group_exists = await self._session.scalar(
            select(
                exists().where(
                    DeviceGroup.id == member.group_id,
                    DeviceGroup.user_id == identity.user_id,
                )
            )
        )
        if not group_exists:
            raise DeviceGroupNotFound(str(member.group_id))
        device_exists = await self._session.scalar(
            select(
                exists().where(
                    Device.id == member.device_id,
                    Device.user_id == identity.user_id,
                    Device.deleted_at.is_(None),
                )
            )
        )
        if not device_exists:
            raise DeviceNotFound(str(member.device_id))

        self._session.add(
            DeviceGroupMember(
                id=member.id,
                group_id=member.group_id,
                device_id=member.device_id,
                created_at=member.created_at,
            )
        )
        try:
            await self._session.flush()
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) == "23505":
                raise DeviceGroupMemberAlreadyExists(
                    str(member.group_id), str(member.device_id)
                ) from error
            raise

    async def delete(
        self, identity: VerifiedIdentity, group_id: UUID, device_id: UUID
    ) -> bool:
        statement = (
            delete(DeviceGroupMember)
            .where(
                DeviceGroupMember.group_id == group_id,
                DeviceGroupMember.device_id == device_id,
                exists(
                    select(DeviceGroup.id).where(
                        DeviceGroup.id == DeviceGroupMember.group_id,
                        DeviceGroup.user_id == identity.user_id,
                    )
                ),
                exists(
                    select(Device.id).where(
                        Device.id == DeviceGroupMember.device_id,
                        Device.user_id == identity.user_id,
                    )
                ),
            )
            .returning(DeviceGroupMember.id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _to_entity(model: DeviceGroupMember) -> DeviceGroupMemberEntity:
        return DeviceGroupMemberEntity(
            entity_id=model.id,
            group_id=model.group_id,
            device_id=model.device_id,
            created_at=model.created_at,
        )
