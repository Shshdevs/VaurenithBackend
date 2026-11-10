from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from tests.support import NoOpUnitOfWork

from app.application.identity import VerifiedIdentity
from app.application.projects.use_cases.projects import CreateProject
from app.application.synchronization import GetUserChangeLog, RecordChange
from app.domain.common.enums import EntityType
from app.domain.identity import EmailAddress, TokenHash
from app.domain.projects.enums import ProjectType
from app.domain.synchronization import ChangeLog, ChangeOperation


def make_identity() -> VerifiedIdentity:
    user_id = uuid4()
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="change-log-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


class ChangeLogRepositoryStub:
    def __init__(self) -> None:
        self.created = []
        self.request = None
        self.changes = []

    async def create(self, change) -> None:
        self.created.append(change)

    async def get_by_user(self, user_id, after_sequence: int, limit: int):
        self.request = (user_id, after_sequence, limit)
        return self.changes


class ProjectRepositoryStub:
    async def create(self, project) -> None:
        self.project = project


@pytest.mark.anyio
async def test_record_change_creates_domain_event_for_authenticated_user() -> None:
    identity = make_identity()
    repository = ChangeLogRepositoryStub()
    use_case = RecordChange(repository)
    entity_id = uuid4()

    await use_case.execute(
        identity,
        EntityType.DEVICE,
        entity_id,
        ChangeOperation.UPDATE,
        4,
        {"name": "worker"},
    )

    event = repository.created[0]
    assert event.user_id == identity.user_id
    assert event.changed_by_user_id == identity.user_id
    assert event.entity_type is EntityType.DEVICE
    assert event.entity_id == entity_id
    assert event.operation is ChangeOperation.UPDATE
    assert event.version == 4
    assert event.payload == {"name": "worker"}


@pytest.mark.anyio
async def test_get_user_change_log_scopes_query_and_cursor() -> None:
    identity = make_identity()
    repository = ChangeLogRepositoryStub()
    use_case = GetUserChangeLog(repository)

    assert await use_case.execute(identity, after_sequence=12, limit=25) == []
    assert repository.request == (identity.user_id, 12, 25)


@pytest.mark.anyio
async def test_get_user_change_log_returns_application_data() -> None:
    identity = make_identity()
    repository = ChangeLogRepositoryStub()
    change = ChangeLog(
        change_log_id=uuid4(),
        user_id=identity.user_id,
        entity_type=EntityType.DEVICE,
        entity_id=uuid4(),
        operation=ChangeOperation.INSERT,
        version=1,
        changed_by_user_id=identity.user_id,
        created_at=datetime.now(UTC),
        sequence=17,
    )
    repository.changes.append(change)
    use_case = GetUserChangeLog(repository)

    result = await use_case.execute(identity)

    assert result[0].id == change.id
    assert result[0].sequence == 17
    assert result[0].entity_id == change.entity_id


@pytest.mark.anyio
async def test_create_project_records_change_as_part_of_application_flow() -> None:
    identity = make_identity()
    change_repository = ChangeLogRepositoryStub()
    use_case = CreateProject(
        ProjectRepositoryStub(), RecordChange(change_repository), NoOpUnitOfWork()
    )

    project = await use_case.execute(
        identity,
        name="Test project",
        project_type=ProjectType.SOFTWARE,
        description="Project description",
    )

    event = change_repository.created[0]
    assert event.entity_id == project.id
    assert event.entity_type is EntityType.PROJECT
    assert event.operation is ChangeOperation.INSERT
    assert event.version == project.version
    assert event.payload == {
        "name": project.name,
        "description": project.description,
        "project_type": project.project_type,
        "status": project.status,
    }
