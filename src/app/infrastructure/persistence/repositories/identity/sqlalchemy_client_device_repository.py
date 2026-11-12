from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.interfaces import ClientDeviceRepository
from app.domain.identity import ClientDevice as ClientDeviceEntity
from app.infrastructure.persistence.models.identity.client_device import (
    ClientDevice as ClientDeviceModel,
)


class SqlAlchemyClientDeviceRepository(ClientDeviceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, device: ClientDeviceEntity) -> None:
        self._session.add(self._to_model(device))
        await self._session.flush()

    async def get_owned(
        self, user_id: UUID, device_id: UUID, for_update: bool = False
    ) -> ClientDeviceEntity | None:
        statement = select(ClientDeviceModel).where(
            ClientDeviceModel.id == device_id,
            ClientDeviceModel.user_id == user_id,
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def list_by_user(self, user_id: UUID) -> list[ClientDeviceEntity]:
        result = await self._session.execute(
            select(ClientDeviceModel)
            .where(ClientDeviceModel.user_id == user_id)
            .order_by(ClientDeviceModel.registered_at.desc(), ClientDeviceModel.id)
        )
        return [self._to_entity(model) for model in result.scalars()]

    async def save(self, device: ClientDeviceEntity) -> None:
        result = await self._session.execute(
            select(ClientDeviceModel).where(
                ClientDeviceModel.id == device.id,
                ClientDeviceModel.user_id == device.user_id,
            )
        )
        model = result.scalar_one()
        model.name = device.name
        model.slug = device.slug
        model.platform = device.platform
        model.app_version = device.app_version
        model.status = device.status
        model.last_seen_at = device.last_seen_at
        model.revoked_at = device.revoked_at
        await self._session.flush()

    @staticmethod
    def _to_model(device: ClientDeviceEntity) -> ClientDeviceModel:
        return ClientDeviceModel(
            id=device.id,
            user_id=device.user_id,
            name=device.name,
            slug=device.slug,
            platform=device.platform,
            app_version=device.app_version,
            status=device.status,
            registered_at=device.registered_at,
            last_seen_at=device.last_seen_at,
            revoked_at=device.revoked_at,
        )

    @staticmethod
    def _to_entity(model: ClientDeviceModel) -> ClientDeviceEntity:
        return ClientDeviceEntity(
            entity_id=model.id,
            user_id=model.user_id,
            name=model.name,
            platform=model.platform,
            app_version=model.app_version,
            status=model.status,
            registered_at=model.registered_at,
            last_seen_at=model.last_seen_at,
            revoked_at=model.revoked_at,
        )
