from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, exists, insert, literal, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DefaultConnectionConflict
from app.application.infrastructure.interfaces import ConnectionRepository
from app.domain.infrastructure import Connection as ConnectionEntity
from app.domain.infrastructure.enums import AuthenticationType, ConnectionStatus
from app.infrastructure.persistence.models import (
    Connection as ConnectionModel,
)
from app.infrastructure.persistence.models import Device


class SqlAlchemyConnectionRepository(ConnectionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, identity: VerifiedIdentity, connection_id: UUID
    ) -> ConnectionEntity | None:
        result = await self._session.execute(
            select(ConnectionModel)
            .join(Device, Device.id == ConnectionModel.device_id)
            .where(
                ConnectionModel.id == connection_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def get_by_user(self, identity: VerifiedIdentity) -> list[ConnectionEntity]:
        result = await self._session.execute(
            select(ConnectionModel)
            .join(Device, Device.id == ConnectionModel.device_id)
            .where(Device.user_id == identity.user_id, Device.deleted_at.is_(None))
            .order_by(ConnectionModel.created_at, ConnectionModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[ConnectionEntity]:
        result = await self._session.execute(
            select(ConnectionModel)
            .join(Device, Device.id == ConnectionModel.device_id)
            .where(
                ConnectionModel.device_id == device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
            .order_by(ConnectionModel.created_at, ConnectionModel.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def create(
        self, identity: VerifiedIdentity, connection: ConnectionEntity
    ) -> bool:
        statement = (
            insert(ConnectionModel)
            .from_select(
                [
                    "id",
                    "device_id",
                    "name",
                    "slug",
                    "host",
                    "port",
                    "username",
                    "authentication_type",
                    "connection_timeout",
                    "is_default",
                    "last_connected_at",
                    "last_status",
                    "last_error",
                    "version",
                    "created_at",
                    "updated_at",
                ],
                select(
                    self._value("id", connection.id),
                    Device.id,
                    self._value("name", connection.name),
                    self._value("slug", connection.slug),
                    self._value("host", connection.host),
                    self._value("port", connection.port),
                    self._value("username", connection.username),
                    self._value("authentication_type", connection.authentication_type),
                    self._value("connection_timeout", connection.connection_timeout),
                    self._value("is_default", connection.is_default),
                    self._value("last_connected_at", connection.last_connected_at),
                    self._value("last_status", connection.last_status),
                    self._value("last_error", None),
                    self._value("version", connection.version),
                    self._value("created_at", connection.created_at),
                    self._value("updated_at", connection.updated_at),
                ).where(
                    Device.id == connection.device_id,
                    Device.user_id == identity.user_id,
                    Device.deleted_at.is_(None),
                ),
            )
            .returning(ConnectionModel.id)
        )
        try:
            result = await self._session.execute(statement)
        except IntegrityError as error:
            raise DefaultConnectionConflict() from error
        return result.scalar_one_or_none() is not None

    async def update(
        self,
        identity: VerifiedIdentity,
        connection: ConnectionEntity,
        expected_version: int,
    ) -> bool:
        owned_device = exists(
            select(Device.id).where(
                Device.id == ConnectionModel.device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
        )
        statement = (
            update(ConnectionModel)
            .where(
                ConnectionModel.id == connection.id,
                ConnectionModel.version == expected_version,
                owned_device,
            )
            .values(
                name=connection.name,
                slug=connection.slug,
                host=connection.host,
                port=connection.port,
                username=connection.username,
                authentication_type=connection.authentication_type,
                connection_timeout=connection.connection_timeout,
                is_default=connection.is_default,
                updated_at=connection.updated_at,
                version=connection.version,
            )
            .returning(ConnectionModel.id)
        )
        try:
            result = await self._session.execute(statement)
        except IntegrityError as error:
            raise DefaultConnectionConflict() from error
        return result.scalar_one_or_none() is not None

    async def update_status(
        self,
        identity: VerifiedIdentity,
        connection_id: UUID,
        expected_version: int,
        status: ConnectionStatus,
        last_connected_at: datetime | None,
        last_error: str | None,
        updated_at: datetime,
    ) -> bool:
        owned_device = exists(
            select(Device.id).where(
                Device.id == ConnectionModel.device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(
            update(ConnectionModel)
            .where(
                ConnectionModel.id == connection_id,
                ConnectionModel.version == expected_version,
                owned_device,
            )
            .values(
                last_status=status,
                last_connected_at=last_connected_at,
                last_error=last_error,
                updated_at=updated_at,
                version=expected_version + 1,
            )
            .returning(ConnectionModel.id)
        )
        return result.scalar_one_or_none() is not None

    async def delete(self, identity: VerifiedIdentity, connection_id: UUID) -> bool:
        owned_device = exists(
            select(Device.id).where(
                Device.id == ConnectionModel.device_id,
                Device.user_id == identity.user_id,
                Device.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(
            delete(ConnectionModel)
            .where(ConnectionModel.id == connection_id, owned_device)
            .returning(ConnectionModel.id)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _value(column_name: str, value: Any) -> ColumnElement[Any]:
        column = ConnectionModel.__table__.c[column_name]
        return literal(value, type_=column.type)

    @staticmethod
    def _to_entity(model: ConnectionModel) -> ConnectionEntity:
        return ConnectionEntity(
            entity_id=model.id,
            device_id=model.device_id,
            name=model.name,
            host=model.host,
            username=model.username,
            authentication_type=AuthenticationType(model.authentication_type),
            created_at=model.created_at,
            updated_at=model.updated_at,
            port=model.port,
            connection_timeout=model.connection_timeout,
            is_default=model.is_default,
            last_connected_at=model.last_connected_at,
            last_status=ConnectionStatus(model.last_status),
            last_error=model.last_error,
            version=model.version,
        )
