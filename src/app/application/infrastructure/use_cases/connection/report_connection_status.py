from datetime import UTC, datetime
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import ConnectionData
from app.application.infrastructure.exceptions import (
    ConnectionNotFound,
    ConnectionVersionConflict,
)
from app.application.infrastructure.interfaces import ConnectionRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.infrastructure import Connection, InvalidConnection
from app.domain.infrastructure.enums import ConnectionStatus
from app.domain.synchronization.enums import ChangeOperation


class ReportConnectionStatus:
    def __init__(
        self,
        connection_repository: ConnectionRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._connection_repository = connection_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(
        self,
        identity: VerifiedIdentity,
        connection_id: UUID,
        expected_version: int,
        status: ConnectionStatus,
        last_error: str | None = None,
        last_connected_at: datetime | None = None,
    ) -> ConnectionData:
        existing = await self._connection_repository.get_by_id(identity, connection_id)
        if existing is None:
            raise ConnectionNotFound(str(connection_id))
        if existing.version != expected_version:
            raise ConnectionVersionConflict(expected_version, existing.version)

        now = datetime.now(UTC)
        connected_at = last_connected_at
        if status is ConnectionStatus.CONNECTED and connected_at is None:
            connected_at = now
        if status is not ConnectionStatus.CONNECTED and connected_at is None:
            connected_at = existing.last_connected_at
        try:
            connection = Connection(
                entity_id=existing.id,
                device_id=existing.device_id,
                name=existing.name,
                host=existing.host,
                username=existing.username,
                authentication_type=existing.authentication_type,
                created_at=existing.created_at,
                updated_at=now,
                port=existing.port,
                connection_timeout=existing.connection_timeout,
                is_default=existing.is_default,
                last_connected_at=connected_at,
                last_status=status,
                last_error=last_error,
                version=expected_version + 1,
            )
        except InvalidConnection as error:
            raise InvalidInput(str(error)) from error

        if not await self._connection_repository.update_status(
            identity,
            connection_id,
            expected_version,
            status,
            connected_at,
            last_error,
            now,
        ):
            latest = await self._connection_repository.get_by_id(identity, connection_id)
            if latest is None:
                raise ConnectionNotFound(str(connection_id))
            raise ConnectionVersionConflict(expected_version, latest.version)

        await self._recorder.execute(
            identity,
            EntityType.CONNECTION,
            connection.id,
            ChangeOperation.UPDATE,
            connection.version,
            {
                "last_status": connection.last_status.value,
                "last_connected_at": connection.last_connected_at.isoformat()
                if connection.last_connected_at is not None
                else None,
            },
        )
        return ConnectionData.from_connection(connection)
