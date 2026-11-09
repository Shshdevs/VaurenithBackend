from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import ProjectDeviceNotFound, ProjectNotFound
from app.application.projects.use_cases.project_devices import (
    DeleteProjectDevice,
    GetDeviceProjects,
    GetProjectDevice,
    GetProjectDevices,
    LinkProjectDevice,
    UpdateProjectDevice,
)
from app.domain.identity import EmailAddress, TokenHash
from app.domain.projects import ProjectDevice, ProjectDeviceRole


class FakeProjectDeviceRepository:
    def __init__(self, project_devices: list[ProjectDevice] | None = None) -> None:
        self.project_devices = {item.id: item for item in project_devices or []}
        self.linked: ProjectDevice | None = None
        self.updated: ProjectDevice | None = None

    async def get_by_id(self, project_device_id: UUID) -> ProjectDevice | None:
        return self.project_devices.get(project_device_id)

    async def get_by_project(self, project_id: UUID) -> list[ProjectDevice]:
        return [
            item for item in self.project_devices.values() if item.project_id == project_id
        ]

    async def get_by_device(self, device_id: UUID) -> list[ProjectDevice]:
        return [
            item for item in self.project_devices.values() if item.device_id == device_id
        ]

    async def link(self, project_device: ProjectDevice) -> None:
        self.linked = project_device
        self.project_devices[project_device.id] = project_device

    async def update(self, project_device: ProjectDevice) -> bool:
        if project_device.id not in self.project_devices:
            return False
        self.updated = project_device
        self.project_devices[project_device.id] = project_device
        return True

    async def delete(self, project_device_id: UUID) -> bool:
        return self.project_devices.pop(project_device_id, None) is not None


class FakeProjectRepository:
    def __init__(self, projects: dict[UUID, UUID] | None = None) -> None:
        self.projects = projects or {}

    async def get_by_id(self, user_id: UUID, project_id: UUID) -> object | None:
        if self.projects.get(project_id) != user_id:
            return None
        return SimpleNamespace(id=project_id)

    async def get_user_projects(self, user_id: UUID) -> list[object]:
        return [
            SimpleNamespace(id=project_id)
            for project_id, owner_id in self.projects.items()
            if owner_id == user_id
        ]


def make_identity(user_id: UUID | None = None) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id or uuid4(),
        email=EmailAddress("project-device-owner@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_project_device(
    project_id: UUID | None = None,
    device_id: UUID | None = None,
    project_device_id: UUID | None = None,
    role: str | None = "deployer",
) -> ProjectDevice:
    return ProjectDevice(
        entity_id=project_device_id or uuid4(),
        project_id=project_id or uuid4(),
        device_id=device_id or uuid4(),
        role=ProjectDeviceRole(role) if role else None,
        created_at=datetime.now(UTC),
    )


@pytest.mark.anyio
async def test_link_project_device_requires_owned_project_and_persists_link() -> None:
    identity = make_identity()
    project_id = uuid4()
    device_id = uuid4()
    repository = FakeProjectDeviceRepository()
    use_case = LinkProjectDevice(
        repository, FakeProjectRepository({project_id: identity.user_id})
    )

    result = await use_case.execute(
        identity=identity, project_id=project_id, device_id=device_id, role=" deployer "
    )

    assert repository.linked is not None
    assert result.id == repository.linked.id
    assert result.project_id == project_id
    assert result.device_id == device_id
    assert result.role == "deployer"


@pytest.mark.anyio
async def test_link_project_device_rejects_unowned_project_and_invalid_role() -> None:
    identity = make_identity()
    repository = FakeProjectDeviceRepository()
    use_case = LinkProjectDevice(repository, FakeProjectRepository())

    with pytest.raises(ProjectNotFound):
        await use_case.execute(
            identity=identity,
            project_id=uuid4(),
            device_id=uuid4(),
            role=None,
        )
    assert repository.linked is None

    project_id = uuid4()
    authorized_use_case = LinkProjectDevice(
        repository, FakeProjectRepository({project_id: identity.user_id})
    )
    with pytest.raises(InvalidInput):
        await authorized_use_case.execute(
            identity=identity,
            project_id=project_id,
            device_id=uuid4(),
            role=" " * 3,
        )
    assert repository.linked is None


@pytest.mark.anyio
async def test_get_project_devices_checks_owner_and_returns_project_links() -> None:
    identity = make_identity()
    project_id = uuid4()
    expected = make_project_device(project_id=project_id)
    other = make_project_device()
    repository = FakeProjectDeviceRepository([expected, other])
    use_case = GetProjectDevices(
        repository, FakeProjectRepository({project_id: identity.user_id})
    )

    result = await use_case.execute(identity=identity, project_id=project_id)

    assert [item.id for item in result] == [expected.id]
    unauthorized = GetProjectDevices(repository, FakeProjectRepository())
    with pytest.raises(ProjectNotFound):
        await unauthorized.execute(identity=identity, project_id=project_id)


@pytest.mark.anyio
async def test_get_device_projects_returns_only_callers_projects() -> None:
    identity = make_identity()
    owned_project_id = uuid4()
    other_project_id = uuid4()
    device_id = uuid4()
    owned = make_project_device(project_id=owned_project_id, device_id=device_id)
    hidden = make_project_device(project_id=other_project_id, device_id=device_id)
    use_case = GetDeviceProjects(
        FakeProjectDeviceRepository([owned, hidden]),
        FakeProjectRepository(
            {owned_project_id: identity.user_id, other_project_id: uuid4()}
        ),
    )

    result = await use_case.execute(identity=identity, device_id=device_id)

    assert [item.id for item in result] == [owned.id]


@pytest.mark.anyio
async def test_get_project_device_requires_project_ownership() -> None:
    identity = make_identity()
    project_id = uuid4()
    project_device = make_project_device(project_id=project_id)
    repository = FakeProjectDeviceRepository([project_device])
    use_case = GetProjectDevice(
        repository, FakeProjectRepository({project_id: identity.user_id})
    )

    result = await use_case.execute(identity=identity, project_device_id=project_device.id)

    assert result.id == project_device.id
    unauthorized = GetProjectDevice(repository, FakeProjectRepository())
    with pytest.raises(ProjectNotFound):
        await unauthorized.execute(identity=identity, project_device_id=project_device.id)
    with pytest.raises(ProjectDeviceNotFound):
        await use_case.execute(identity=identity, project_device_id=uuid4())


@pytest.mark.anyio
async def test_update_project_device_checks_both_projects_and_preserves_link_id() -> None:
    identity = make_identity()
    current_project_id = uuid4()
    target_project_id = uuid4()
    project_device = make_project_device(project_id=current_project_id)
    repository = FakeProjectDeviceRepository([project_device])
    project_repository = FakeProjectRepository(
        {current_project_id: identity.user_id, target_project_id: identity.user_id}
    )
    use_case = UpdateProjectDevice(repository, project_repository)

    result = await use_case.execute(
        identity=identity,
        project_device_id=project_device.id,
        project_id=target_project_id,
        device_id=uuid4(),
        role="operator",
    )

    assert repository.updated is not None
    assert result.id == project_device.id
    assert result.project_id == target_project_id
    assert result.created_at == project_device.created_at
    assert result.role == "operator"

    unauthorized = UpdateProjectDevice(repository, FakeProjectRepository())
    with pytest.raises(ProjectNotFound):
        await unauthorized.execute(
            identity=identity,
            project_device_id=project_device.id,
            project_id=target_project_id,
            device_id=uuid4(),
            role=None,
        )


@pytest.mark.anyio
async def test_delete_project_device_checks_owner_and_reports_missing() -> None:
    identity = make_identity()
    project_id = uuid4()
    project_device = make_project_device(project_id=project_id)
    repository = FakeProjectDeviceRepository([project_device])
    use_case = DeleteProjectDevice(
        repository, FakeProjectRepository({project_id: identity.user_id})
    )

    await use_case.execute(identity=identity, project_device_id=project_device.id)
    assert project_device.id not in repository.project_devices
    with pytest.raises(ProjectDeviceNotFound):
        await use_case.execute(identity=identity, project_device_id=project_device.id)

    unauthorized_repository = FakeProjectDeviceRepository([project_device])
    unauthorized = DeleteProjectDevice(unauthorized_repository, FakeProjectRepository())
    with pytest.raises(ProjectNotFound):
        await unauthorized.execute(identity=identity, project_device_id=project_device.id)
    assert project_device.id in unauthorized_repository.project_devices
