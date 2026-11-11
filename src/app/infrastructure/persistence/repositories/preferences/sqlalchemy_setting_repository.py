from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.preferences.interfaces import SettingRepository
from app.domain.preferences import Setting as SettingEntity
from app.domain.preferences import SettingScope
from app.infrastructure.persistence.models.identity.client_device import ClientDevice
from app.infrastructure.persistence.models.preferences.setting import Setting


class SqlAlchemySettingRepository(SettingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID, setting_id: UUID) -> SettingEntity | None:
        result = await self._session.execute(
            select(Setting).where(Setting.user_id == user_id, Setting.id == setting_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def get_for_scope(
        self, user_id: UUID, scope: SettingScope, client_device_id: UUID | None
    ) -> list[SettingEntity]:
        result = await self._session.execute(
            select(Setting)
            .where(
                Setting.user_id == user_id,
                Setting.scope == scope,
                Setting.client_device_id.is_(None)
                if client_device_id is None
                else Setting.client_device_id == client_device_id,
            )
            .order_by(Setting.key)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def owns_client_device(self, user_id: UUID, client_device_id: UUID) -> bool:
        result = await self._session.execute(
            select(ClientDevice.id).where(
                ClientDevice.id == client_device_id, ClientDevice.user_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def create(self, setting: SettingEntity) -> bool:
        statement = (
            insert(Setting)
            .values(**self._values(setting))
            .on_conflict_do_nothing()
            .returning(Setting.id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def update(self, setting: SettingEntity, expected_version: int) -> bool:
        result = await self._session.execute(
            update(Setting)
            .where(
                Setting.user_id == setting.user_id,
                Setting.id == setting.id,
                Setting.version == expected_version,
            )
            .values(
                value=setting.value, version=setting.version, updated_at=setting.updated_at
            )
            .returning(Setting.id)
        )
        return result.scalar_one_or_none() is not None

    async def delete(self, user_id: UUID, setting_id: UUID, expected_version: int) -> bool:
        result = await self._session.execute(
            delete(Setting)
            .where(
                Setting.user_id == user_id,
                Setting.id == setting_id,
                Setting.version == expected_version,
            )
            .returning(Setting.id)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _values(setting: SettingEntity) -> dict:
        return {
            "id": setting.id,
            "user_id": setting.user_id,
            "client_device_id": setting.client_device_id,
            "scope": setting.scope,
            "key": setting.key,
            "value": setting.value,
            "version": setting.version,
            "created_at": setting.created_at,
            "updated_at": setting.updated_at,
        }

    @staticmethod
    def _to_entity(model: Setting) -> SettingEntity:
        return SettingEntity(
            model.id,
            model.user_id,
            model.scope,
            model.key,
            model.created_at,
            model.updated_at,
            model.client_device_id,
            model.value,
            model.version,
        )
