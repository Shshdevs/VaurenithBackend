from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.application.identity import VerifiedIdentity
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure import Container, ContainerName, ContainerRuntimeId


class FakeContainerRepository:
    def __init__(self) -> None:
        self.containers: dict[UUID, Container] = {}
        self.device_owners: dict[UUID, UUID] = {}
        self.deleted_devices: set[UUID] = set()
        self.project_owners: dict[UUID, UUID] = {}
        self.environment_projects: dict[UUID, UUID] = {}
        self.services: dict[UUID, tuple[UUID, UUID | None, UUID | None]] = {}

    def _visible(self, identity: VerifiedIdentity, container: Container) -> bool:
        return (
            self.device_owners.get(container.device_id) == identity.user_id
            and container.device_id not in self.deleted_devices
        )

    def _valid_associations(self, identity: VerifiedIdentity, container: Container) -> bool:
        if not self._visible(identity, container):
            return False
        if (
            container.project_id is not None
            and self.project_owners.get(container.project_id) != identity.user_id
        ):
            return False
        if container.environment_id is not None:
            project_id = self.environment_projects.get(container.environment_id)
            if project_id is None or project_id != container.project_id:
                return False
            if self.project_owners.get(project_id) != identity.user_id:
                return False
        return container.service_id is None or self.services.get(container.service_id) == (
            container.device_id,
            container.project_id,
            container.environment_id,
        )

    async def get_by_user(self, identity: VerifiedIdentity) -> list[Container]:
        return [
            container
            for container in self.containers.values()
            if self._visible(identity, container)
        ]

    async def get_by_id(
        self, identity: VerifiedIdentity, container_id: UUID
    ) -> Container | None:
        container = self.containers.get(container_id)
        return (
            container
            if container is not None and self._visible(identity, container)
            else None
        )

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[Container]:
        if self.device_owners.get(device_id) != identity.user_id:
            return []
        return [
            container
            for container in self.containers.values()
            if container.device_id == device_id and self._visible(identity, container)
        ]

    async def get_by_service(
        self, identity: VerifiedIdentity, service_id: UUID
    ) -> list[Container]:
        service = self.services.get(service_id)
        if service is None or self.device_owners.get(service[0]) != identity.user_id:
            return []
        return [
            container
            for container in self.containers.values()
            if container.service_id == service_id
            and container.device_id == service[0]
            and self._visible(identity, container)
        ]

    async def get_by_project(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[Container]:
        if self.project_owners.get(project_id) != identity.user_id:
            return []
        return [
            container
            for container in self.containers.values()
            if container.project_id == project_id and self._visible(identity, container)
        ]

    async def get_by_environment(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> list[Container]:
        project_id = self.environment_projects.get(environment_id)
        if project_id is None or self.project_owners.get(project_id) != identity.user_id:
            return []
        return [
            container
            for container in self.containers.values()
            if container.environment_id == environment_id
            and container.project_id == project_id
            and self._visible(identity, container)
        ]

    async def create(self, identity: VerifiedIdentity, container: Container) -> bool:
        if not self._valid_associations(identity, container):
            return False
        self.containers[container.id] = container
        return True

    async def update(
        self, identity: VerifiedIdentity, container: Container, expected_version: int
    ) -> bool:
        existing = await self.get_by_id(identity, container.id)
        if (
            existing is None
            or existing.version != expected_version
            or not self._valid_associations(identity, container)
        ):
            return False
        self.containers[container.id] = container
        return True

    async def delete(self, identity: VerifiedIdentity, container_id: UUID) -> bool:
        if await self.get_by_id(identity, container_id) is None:
            return False
        del self.containers[container_id]
        return True


class RecordingChangeRecorder:
    def __init__(self) -> None:
        self.events: list[tuple[tuple[object, ...], dict[str, object]]] = []

    async def execute(self, *args: object, **kwargs: object) -> None:
        self.events.append((args, kwargs))


def make_container_identity(user_id: UUID | None = None) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id or uuid4(),
        email=EmailAddress("container-owner@example.test"),
        auth_provider="container-test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("f" * 64),
    )


def add_owned_container_associations(
    repository: FakeContainerRepository, identity: VerifiedIdentity
) -> tuple[UUID, UUID, UUID, UUID]:
    device_id = uuid4()
    project_id = uuid4()
    environment_id = uuid4()
    service_id = uuid4()
    repository.device_owners[device_id] = identity.user_id
    repository.project_owners[project_id] = identity.user_id
    repository.environment_projects[environment_id] = project_id
    repository.services[service_id] = (device_id, project_id, environment_id)
    return device_id, project_id, environment_id, service_id


def make_container(
    device_id: UUID,
    project_id: UUID | None = None,
    environment_id: UUID | None = None,
    service_id: UUID | None = None,
    name: str = "api",
    version: int = 1,
) -> Container:
    now = datetime.now(UTC)
    return Container(
        entity_id=uuid4(),
        device_id=device_id,
        project_id=project_id,
        environment_id=environment_id,
        service_id=service_id,
        container_runtime_id=ContainerRuntimeId("docker:api-123"),
        name=ContainerName(name),
        image=None,
        created_at=now,
        updated_at=now,
        version=version,
    )
