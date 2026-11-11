from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import ConnectionData
from app.application.infrastructure.exceptions import ConnectionDeviceNotFound
from app.application.infrastructure.interfaces import ConnectionRepository
from app.application.infrastructure.use_cases.connection.change_payload import (
    connection_change_payload,
)
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.infrastructure import Connection, InvalidConnection
from app.domain.infrastructure.enums import AuthenticationType
from app.domain.synchronization.enums import ChangeOperation


class CreateConnection:
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
        device_id: UUID,
        name: str,
        host: str,
        username: str,
        authentication_type: AuthenticationType,
        port: int = 22,
        connection_timeout: int = 30,
        is_default: bool = False,
    ) -> ConnectionData:
        now = datetime.now(UTC)
        try:
            connection = Connection(
                entity_id=uuid4(),
                device_id=device_id,
                name=name,
                host=host,
                username=username,
                authentication_type=authentication_type,
                created_at=now,
                updated_at=now,
                port=port,
                connection_timeout=connection_timeout,
                is_default=is_default,
            )
        except InvalidConnection as error:
            raise InvalidInput(str(error)) from error

        if not await self._connection_repository.create(identity, connection):
            raise ConnectionDeviceNotFound(str(device_id))

        await self._recorder.execute(
            identity,
            EntityType.CONNECTION,
            connection.id,
            ChangeOperation.INSERT,
            connection.version,
            connection_change_payload(connection),
        )
        return ConnectionData.from_connection(connection)
