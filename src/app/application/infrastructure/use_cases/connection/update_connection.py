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
    DefaultConnectionConflict,
)
from app.application.infrastructure.interfaces import ConnectionRepository
from app.application.infrastructure.use_cases.connection.change_payload import (
    connection_change_payload,
)
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.infrastructure import Connection, InvalidConnection
from app.domain.infrastructure.enums import AuthenticationType
from app.domain.synchronization.enums import ChangeOperation


class UpdateConnection:
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
        name: str,
        host: str,
        username: str,
        authentication_type: AuthenticationType,
        port: int = 22,
        connection_timeout: int = 30,
        is_default: bool = False,
    ) -> ConnectionData:
        existing = await self._connection_repository.get_by_id(identity, connection_id)
        if existing is None:
            raise ConnectionNotFound(str(connection_id))
        if existing.version != expected_version:
            raise ConnectionVersionConflict(expected_version, existing.version)

        now = datetime.now(UTC)
        try:
            connection = Connection(
                entity_id=existing.id,
                device_id=existing.device_id,
                name=name,
                host=host,
                username=username,
                authentication_type=authentication_type,
                created_at=existing.created_at,
                updated_at=now,
                port=port,
                connection_timeout=connection_timeout,
                is_default=is_default,
                last_connected_at=existing.last_connected_at,
                last_status=existing.last_status,
                last_error=existing.last_error,
                version=expected_version + 1,
            )
        except InvalidConnection as error:
            raise InvalidInput(str(error)) from error

        try:
            updated = await self._connection_repository.update(
                identity, connection, expected_version
            )
        except DefaultConnectionConflict:
            raise
        if not updated:
            latest = await self._connection_repository.get_by_id(identity, connection_id)
            if latest is None:
                raise ConnectionNotFound(str(connection_id))
            if latest.version != expected_version:
                raise ConnectionVersionConflict(expected_version, latest.version)
            raise ConnectionNotFound(str(connection_id))

        await self._recorder.execute(
            identity,
            EntityType.CONNECTION,
            connection.id,
            ChangeOperation.UPDATE,
            connection.version,
            connection_change_payload(connection),
        )
        return ConnectionData.from_connection(connection)
