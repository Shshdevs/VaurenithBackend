from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from tests.support import NoOpRecordChange

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import (
    ServiceAssociationNotFound,
    ServiceNotFound,
    ServiceVersionConflict,
)
from app.application.infrastructure.use_cases.service import (
    CreateService,
    GetDeviceServices,
    GetEnvironmentServices,
    GetProjectServices,
    GetService,
    UpdateService,
    UpdateServiceStatus,
)
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure import Service
from app.domain.infrastructure.enums import ResourceStatus, ServiceType


class FakeServiceRepository:
    def __init__(self) -> None:
        self.services: dict[UUID, Service] = {}
        self.device_owners: dict[UUID, UUID] = {}
        self.project_owners: dict[UUID, UUID] = {}
        self.environment_projects: dict[UUID, UUID] = {}

    async def get_by_user(self, identity: VerifiedIdentity) -> list[Service]:
        return [
            service
            for service in self.services.values()
            if self.device_owners.get(service.device_id) == identity.user_id
        ]

    def _has_valid_associations(self, identity: VerifiedIdentity, service: Service) -> bool:
        if self.device_owners.get(service.device_id) != identity.user_id:
            return False
        if (
            service.project_id is not None
            and self.project_owners.get(service.project_id) != identity.user_id
        ):
            return False
        if service.environment_id is not None:
            environment_project = self.environment_projects.get(service.environment_id)
            if environment_project is None:
                return False
            if self.project_owners.get(environment_project) != identity.user_id:
                return False
            if service.project_id is not None and environment_project != service.project_id:
                return False
        return True

    async def get_by_id(
        self, identity: VerifiedIdentity, service_id: UUID
    ) -> Service | None:
        service = self.services.get(service_id)
        if service is None or self.device_owners.get(service.device_id) != identity.user_id:
            return None
        return service

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[Service]:
        if self.device_owners.get(device_id) != identity.user_id:
            return []
        return [
            service for service in self.services.values() if service.device_id == device_id
        ]

    async def get_by_project(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[Service]:
        if self.project_owners.get(project_id) != identity.user_id:
            return []
        return [
            service
            for service in self.services.values()
            if service.project_id == project_id
            and self.device_owners.get(service.device_id) == identity.user_id
        ]

    async def get_by_environment(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> list[Service]:
        project_id = self.environment_projects.get(environment_id)
        if project_id is None or self.project_owners.get(project_id) != identity.user_id:
            return []
        return [
            service
            for service in self.services.values()
            if service.environment_id == environment_id
            and self.device_owners.get(service.device_id) == identity.user_id
        ]

    async def create(self, identity: VerifiedIdentity, service: Service) -> bool:
        if not self._has_valid_associations(identity, service):
            return False
        self.services[service.id] = service
        return True

    async def update(
        self, identity: VerifiedIdentity, service: Service, expected_version: int
    ) -> bool:
        existing = await self.get_by_id(identity, service.id)
        if (
            existing is None
            or existing.version != expected_version
            or not self._has_valid_associations(identity, service)
        ):
            return False
        self.services[service.id] = service
        return True

    async def delete(self, identity: VerifiedIdentity, service_id: UUID) -> bool:
        if await self.get_by_id(identity, service_id) is None:
            return False
        del self.services[service_id]
        return True


def make_identity(user_id: UUID | None = None) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id or uuid4(),
        email=EmailAddress("service-owner@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("c" * 64),
    )


def configure_owned_associations(
    repository: FakeServiceRepository, identity: VerifiedIdentity
) -> tuple[UUID, UUID, UUID]:
    device_id = uuid4()
    project_id = uuid4()
    environment_id = uuid4()
    repository.device_owners[device_id] = identity.user_id
    repository.project_owners[project_id] = identity.user_id
    repository.environment_projects[environment_id] = project_id
    return device_id, project_id, environment_id


@pytest.mark.anyio
async def test_create_service_builds_value_objects_and_binds_service_to_owned_parents() -> (
    None
):
    identity = make_identity()
    repository = FakeServiceRepository()
    device_id, project_id, environment_id = configure_owned_associations(
        repository, identity
    )

    result = await CreateService(repository, NoOpRecordChange()).execute(
        identity=identity,
        device_id=device_id,
        project_id=project_id,
        environment_id=environment_id,
        name=" api ",
        service_type=ServiceType.APPLICATION,
        system_identifier=" systemd:api ",
        metadata={"port": 8080},
    )

    assert result.device_id == device_id
    assert result.project_id == project_id
    assert result.environment_id == environment_id
    assert result.name == "api"
    assert result.system_identifier == "systemd:api"
    assert result.status is ResourceStatus.UNKNOWN
    assert result.version == 1


@pytest.mark.anyio
async def test_create_service_rejects_invalid_input_and_foreign_associations() -> None:
    identity = make_identity()
    repository = FakeServiceRepository()
    device_id, project_id, _ = configure_owned_associations(repository, identity)
    use_case = CreateService(repository, NoOpRecordChange())

    with pytest.raises(InvalidInput):
        await use_case.execute(
            identity=identity,
            device_id=device_id,
            name="  ",
            service_type=ServiceType.APPLICATION,
        )

    with pytest.raises(ServiceAssociationNotFound):
        await use_case.execute(
            identity=identity,
            device_id=uuid4(),
            project_id=project_id,
            name="api",
            service_type=ServiceType.APPLICATION,
        )
    assert repository.services == {}


@pytest.mark.anyio
async def test_service_get_and_parent_lists_are_owner_scoped() -> None:
    identity = make_identity()
    repository = FakeServiceRepository()
    device_id, project_id, environment_id = configure_owned_associations(
        repository, identity
    )
    service = await CreateService(repository, NoOpRecordChange()).execute(
        identity=identity,
        device_id=device_id,
        project_id=project_id,
        environment_id=environment_id,
        name="api",
        service_type=ServiceType.APPLICATION,
    )

    assert (await GetService(repository).execute(identity, service.id)).id == service.id
    assert [
        item.id for item in await GetDeviceServices(repository).execute(identity, device_id)
    ] == [service.id]
    assert [
        item.id
        for item in await GetProjectServices(repository).execute(identity, project_id)
    ] == [service.id]
    assert [
        item.id
        for item in await GetEnvironmentServices(repository).execute(
            identity, environment_id
        )
    ] == [service.id]
    with pytest.raises(ServiceNotFound):
        await GetService(repository).execute(make_identity(), service.id)
    assert await GetProjectServices(repository).execute(make_identity(), project_id) == []


@pytest.mark.anyio
async def test_update_service_preserves_status_and_uses_optimistic_version() -> None:
    identity = make_identity()
    repository = FakeServiceRepository()
    device_id, project_id, environment_id = configure_owned_associations(
        repository, identity
    )
    created = await CreateService(repository, NoOpRecordChange()).execute(
        identity=identity,
        device_id=device_id,
        project_id=project_id,
        environment_id=environment_id,
        name="api",
        service_type=ServiceType.APPLICATION,
    )
    running = await UpdateServiceStatus(repository, NoOpRecordChange()).execute(
        identity, created.id, expected_version=1, status=ResourceStatus.RUNNING
    )
    updated = await UpdateService(repository, NoOpRecordChange()).execute(
        identity=identity,
        service_id=created.id,
        expected_version=2,
        device_id=device_id,
        project_id=project_id,
        environment_id=environment_id,
        name="api-v2",
        service_type=ServiceType.APPLICATION,
        metadata={"port": 8081},
    )

    assert updated.version == 3
    assert updated.status is ResourceStatus.RUNNING
    assert updated.last_status_at == running.last_status_at
    assert updated.name == "api-v2"
    assert updated.created_at == created.created_at

    with pytest.raises(ServiceVersionConflict):
        await UpdateService(repository, NoOpRecordChange()).execute(
            identity=identity,
            service_id=created.id,
            expected_version=2,
            device_id=device_id,
            project_id=project_id,
            environment_id=environment_id,
            name="stale",
            service_type=ServiceType.APPLICATION,
        )


@pytest.mark.anyio
async def test_update_service_status_reports_missing_and_invalid_status() -> None:
    identity = make_identity()
    repository = FakeServiceRepository()
    use_case = UpdateServiceStatus(repository, NoOpRecordChange())
    with pytest.raises(ServiceNotFound):
        await use_case.execute(identity, uuid4(), 1, ResourceStatus.RUNNING)
