from datetime import datetime
from uuid import UUID

from sqlalchemy import Exists, delete, exists, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.synchronization.exceptions import (
    SyncStateAlreadyExists,
    SyncStateDeletionConflict,
)
from app.application.synchronization.interfaces import SyncStateRepository
from app.domain.synchronization import SyncState as SyncStateEntity
from app.infrastructure.persistence.models import ClientDevice, SyncState


class SqlAlchemySyncStateRepository(SyncStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_sync_state(
        self, user_id: UUID, sync_state_id: UUID
    ) -> SyncStateEntity | None:
        result = await self._session.execute(
            select(SyncState).where(
                self._owned_sync_state(user_id=user_id, sync_state_id=sync_state_id)
            )
        )
        sync_state = result.scalar_one_or_none()
        return self._to_entity(sync_state) if sync_state else None

    async def create(self, sync_state: SyncStateEntity) -> bool:
        owns_client_device = await self._session.scalar(
            select(
                exists().where(
                    ClientDevice.id == sync_state.client_device_id,
                    ClientDevice.user_id == sync_state.user_id,
                )
            )
        )
        if not owns_client_device:
            return False
        self._session.add(self._to_model(sync_state))
        try:
            await self._session.flush()
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) == "23505":
                raise SyncStateAlreadyExists() from error
            raise
        return True

    async def update(
        self,
        user_id: UUID,
        sync_state: SyncStateEntity,
        expected_version: int | None,
        expected_updated_at: datetime,
    ) -> bool:
        version_condition = (
            SyncState.local_version.is_(None)
            if expected_version is None
            else SyncState.local_version == expected_version
        )
        statement = (
            update(SyncState)
            .where(
                self._owned_sync_state(user_id, sync_state.id),
                self._owned_client_device(user_id, sync_state.client_device_id),
                version_condition,
                SyncState.updated_at == expected_updated_at,
            )
            .values(
                client_device_id=sync_state.client_device_id,
                entity_type=sync_state.entity_type,
                entity_id=sync_state.entity_id,
                local_version=sync_state.local_version,
                server_version=sync_state.server_version,
                status=sync_state.status,
                last_error=sync_state.last_error,
                last_synced_at=sync_state.last_synced_at,
                updated_at=sync_state.updated_at,
                version=SyncState.version + 1,
            )
            .returning(SyncState.id)
        )

        result = await self._session.execute(statement)
        updated_id = result.scalar_one_or_none()
        return updated_id is not None

    async def delete(self, user_id: UUID, sync_state_id: UUID) -> bool:
        statement = (
            delete(SyncState)
            .where(self._owned_sync_state(user_id, sync_state_id))
            .returning(SyncState.id)
        )

        try:
            result = await self._session.execute(statement)
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) == "23503":
                raise SyncStateDeletionConflict(str(sync_state_id)) from error
            raise

        return result.scalar_one_or_none() is not None

    @staticmethod
    def _owned_sync_state(user_id: UUID, sync_state_id: UUID) -> Exists:
        return exists(
            select(SyncState.id).where(
                SyncState.id == sync_state_id,
                SyncState.user_id == user_id,
            )
        )

    @staticmethod
    def _owned_client_device(user_id: UUID, client_device_id: UUID) -> Exists:
        return exists(
            select(ClientDevice.id).where(
                ClientDevice.id == client_device_id,
                ClientDevice.user_id == user_id,
            )
        )

    @staticmethod
    def _to_model(entity: SyncStateEntity) -> SyncState:
        return SyncState(
            sync_state_id=entity.id,
            user_id=entity.user_id,
            client_device_id=entity.client_device_id,
            entity_type=entity.entity_type,
            entity_id=entity.entity_id,
            updated_at=entity.updated_at,
            local_version=entity.local_version,
            server_version=entity.server_version,
            status=entity.status,
            last_synced_at=entity.last_synced_at,
            last_error=entity.last_error,
            version=entity.version,
        )

    @staticmethod
    def _to_entity(model: SyncState) -> SyncStateEntity:
        return SyncStateEntity(
            sync_state_id=model.id,
            user_id=model.user_id,
            client_device_id=model.client_device_id,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            updated_at=model.updated_at,
            local_version=model.local_version,
            server_version=model.server_version,
            status=model.status,
            last_synced_at=model.last_synced_at,
            last_error=model.last_error,
            version=model.version,
        )
