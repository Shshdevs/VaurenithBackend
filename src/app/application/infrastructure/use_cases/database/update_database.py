from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DatabaseData
from app.application.infrastructure.exceptions import (
    DatabaseAssociationNotFound,
    DatabaseNotFound,
    DatabaseVersionConflict,
)
from app.application.infrastructure.interfaces import DatabaseRepository
from app.application.infrastructure.use_cases.database.change_payload import (
    database_change_payload,
)
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.infrastructure import (
    Database,
    DatabaseCatalogName,
    DatabaseEndpoint,
    DatabaseResourceName,
    InvalidDatabase,
)
from app.domain.infrastructure.enums import DbmsType, ResourceStatus
from app.domain.synchronization.enums import ChangeOperation


class UpdateDatabase:
    def __init__(
        self,
        database_repository: DatabaseRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._database_repository = database_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(
        self,
        identity: VerifiedIdentity,
        database_id: UUID,
        expected_version: int,
        device_id: UUID,
        name: str,
        dbms_type: DbmsType,
        status: ResourceStatus,
        project_id: UUID | None = None,
        environment_id: UUID | None = None,
        container_id: UUID | None = None,
        service_id: UUID | None = None,
        host: str | None = None,
        port: int | None = None,
        database_name: str | None = None,
        last_checked_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DatabaseData:
        existing = await self._database_repository.get_by_id(identity, database_id)
        if existing is None:
            raise DatabaseNotFound(str(database_id))
        if existing.version != expected_version:
            raise DatabaseVersionConflict(expected_version, existing.version)

        try:
            endpoint = (
                DatabaseEndpoint(host=host, port=port)
                if host is not None or port is not None
                else None
            )
            database = Database(
                entity_id=existing.id,
                device_id=device_id,
                name=DatabaseResourceName(name),
                dbms_type=dbms_type,
                created_at=existing.created_at,
                updated_at=datetime.now(UTC),
                project_id=project_id,
                environment_id=environment_id,
                container_id=container_id,
                service_id=service_id,
                endpoint=endpoint,
                database_name=(
                    DatabaseCatalogName(database_name)
                    if database_name is not None
                    else None
                ),
                status=status,
                last_checked_at=last_checked_at,
                metadata=metadata,
                version=expected_version + 1,
            )
        except InvalidDatabase as error:
            raise InvalidInput(str(error)) from error

        updated = await self._database_repository.update(
            identity, database, expected_version
        )
        if not updated:
            latest = await self._database_repository.get_by_id(identity, database_id)
            if latest is None:
                raise DatabaseNotFound(str(database_id))
            if latest.version != expected_version:
                raise DatabaseVersionConflict(expected_version, latest.version)
            raise DatabaseAssociationNotFound()

        await self._recorder.execute(
            identity,
            EntityType.DATABASE,
            database.id,
            ChangeOperation.UPDATE,
            database.version,
            database_change_payload(database),
        )
        return DatabaseData.from_database(database)
