from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.application.identity import VerifiedIdentity
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure import (
    Database,
    DatabaseResourceName,
)
from app.domain.infrastructure.enums import DbmsType


class FakeDatabaseRepository:
    def __init__(self) -> None:
        self.databases: dict[UUID, Database] = {}
        self.device_owners: dict[UUID, UUID] = {}
        self.deleted_devices: set[UUID] = set()
        self.project_owners: dict[UUID, UUID] = {}
        self.environment_projects: dict[UUID, UUID] = {}
        self.containers: dict[UUID, tuple[UUID, UUID | None, UUID | None, UUID | None]] = {}
        self.services: dict[UUID, tuple[UUID, UUID | None, UUID | None]] = {}

    def _visible(self, identity: VerifiedIdentity, database: Database) -> bool:
        return (
            self.device_owners.get(database.device_id) == identity.user_id
            and database.device_id not in self.deleted_devices
        )

    def _valid_associations(self, identity: VerifiedIdentity, database: Database) -> bool:
        if not self._visible(identity, database):
            return False
        if (
            database.project_id is not None
            and self.project_owners.get(database.project_id) != identity.user_id
        ):
            return False
        if database.environment_id is not None:
            project_id = self.environment_projects.get(database.environment_id)
            if (
                project_id is None
                or project_id != database.project_id
                or self.project_owners.get(project_id) != identity.user_id
            ):
                return False
        if database.container_id is not None:
            container = self.containers.get(database.container_id)
            if container != (
                database.device_id,
                database.project_id,
                database.environment_id,
                database.service_id,
            ):
                return False
        return database.service_id is None or self.services.get(database.service_id) == (
            database.device_id,
            database.project_id,
            database.environment_id,
        )

    async def get_by_user(self, identity: VerifiedIdentity) -> list[Database]:
        return [
            database
            for database in self.databases.values()
            if self._visible(identity, database)
        ]

    async def get_by_id(
        self, identity: VerifiedIdentity, database_id: UUID
    ) -> Database | None:
        database = self.databases.get(database_id)
        if database is None or not self._visible(identity, database):
            return None
        return database

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[Database]:
        if self.device_owners.get(device_id) != identity.user_id:
            return []
        return [
            database
            for database in self.databases.values()
            if database.device_id == device_id and self._visible(identity, database)
        ]

    async def get_by_project(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[Database]:
        if self.project_owners.get(project_id) != identity.user_id:
            return []
        return [
            database
            for database in self.databases.values()
            if database.project_id == project_id and self._visible(identity, database)
        ]

    async def get_by_environment(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> list[Database]:
        project_id = self.environment_projects.get(environment_id)
        if project_id is None or self.project_owners.get(project_id) != identity.user_id:
            return []
        return [
            database
            for database in self.databases.values()
            if database.environment_id == environment_id
            and database.project_id == project_id
            and self._visible(identity, database)
        ]

    async def get_by_container(
        self, identity: VerifiedIdentity, container_id: UUID
    ) -> list[Database]:
        container = self.containers.get(container_id)
        if container is None or self.device_owners.get(container[0]) != identity.user_id:
            return []
        return [
            database
            for database in self.databases.values()
            if database.container_id == container_id
            and self._valid_associations(identity, database)
        ]

    async def get_by_service(
        self, identity: VerifiedIdentity, service_id: UUID
    ) -> list[Database]:
        service = self.services.get(service_id)
        if service is None or self.device_owners.get(service[0]) != identity.user_id:
            return []
        return [
            database
            for database in self.databases.values()
            if database.service_id == service_id
            and self._valid_associations(identity, database)
        ]

    async def create(self, identity: VerifiedIdentity, database: Database) -> bool:
        if not self._valid_associations(identity, database):
            return False
        self.databases[database.id] = database
        return True

    async def update(
        self, identity: VerifiedIdentity, database: Database, expected_version: int
    ) -> bool:
        existing = await self.get_by_id(identity, database.id)
        if (
            existing is None
            or existing.version != expected_version
            or not self._valid_associations(identity, database)
        ):
            return False
        self.databases[database.id] = database
        return True

    async def delete(self, identity: VerifiedIdentity, database_id: UUID) -> bool:
        if await self.get_by_id(identity, database_id) is None:
            return False
        del self.databases[database_id]
        return True


class RecordingDatabaseChangeRecorder:
    def __init__(self) -> None:
        self.events: list[tuple[tuple[object, ...], dict[str, object]]] = []

    async def execute(self, *args: object, **kwargs: object) -> None:
        self.events.append((args, kwargs))


def make_database_identity(user_id: UUID | None = None) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id or uuid4(),
        email=EmailAddress("database-owner@example.test"),
        auth_provider="database-test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("b" * 64),
    )


def add_owned_database_associations(
    repository: FakeDatabaseRepository, identity: VerifiedIdentity
) -> tuple[UUID, UUID, UUID, UUID, UUID]:
    device_id = uuid4()
    project_id = uuid4()
    environment_id = uuid4()
    service_id = uuid4()
    container_id = uuid4()
    repository.device_owners[device_id] = identity.user_id
    repository.project_owners[project_id] = identity.user_id
    repository.environment_projects[environment_id] = project_id
    repository.services[service_id] = (device_id, project_id, environment_id)
    repository.containers[container_id] = (
        device_id,
        project_id,
        environment_id,
        service_id,
    )
    return device_id, project_id, environment_id, container_id, service_id


def make_database(
    device_id: UUID,
    project_id: UUID | None = None,
    environment_id: UUID | None = None,
    container_id: UUID | None = None,
    service_id: UUID | None = None,
    name: str = "primary",
    version: int = 1,
) -> Database:
    now = datetime.now(UTC)
    return Database(
        entity_id=uuid4(),
        device_id=device_id,
        project_id=project_id,
        environment_id=environment_id,
        container_id=container_id,
        service_id=service_id,
        name=DatabaseResourceName(name),
        dbms_type=DbmsType.POSTGRESQL,
        created_at=now,
        updated_at=now,
        version=version,
    )
