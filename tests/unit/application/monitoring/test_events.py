from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from tests.support import NoOpUnitOfWork

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DeviceNotFound
from app.application.monitoring import CreateEvent, GetUserEvents
from app.application.monitoring.exceptions import EventClientDeviceNotFound
from app.application.projects.exceptions import ProjectNotFound
from app.domain.identity import EmailAddress, TokenHash
from app.domain.monitoring import Event, EventResult, EventType


class DeviceRepositoryStub:
    def __init__(self, device_ids: set[UUID]) -> None:
        self.device_ids = device_ids

    async def get_by_id(self, identity: VerifiedIdentity, device_id: UUID):
        return object() if device_id in self.device_ids else None


class ProjectRepositoryStub:
    def __init__(self, project_ids: set[UUID]) -> None:
        self.project_ids = project_ids

    async def get_by_id(self, user_id: UUID, project_id: UUID):
        return object() if project_id in self.project_ids else None


class EventRepositoryStub:
    def __init__(self, client_device_ids: set[UUID] | None = None) -> None:
        self.client_device_ids = client_device_ids or set()
        self.events: list[Event] = []

    async def create(self, event: Event) -> None:
        self.events.append(event)

    async def owns_client_device(self, user_id: UUID, client_device_id: UUID) -> bool:
        return client_device_id in self.client_device_ids

    async def get_user_events(
        self, user_id, project_id, device_id, event_type, result, start, end, limit, offset
    ) -> list[Event]:
        filtered = [event for event in self.events if event.user_id == user_id]
        if project_id is not None:
            filtered = [event for event in filtered if event.project_id == project_id]
        if device_id is not None:
            filtered = [event for event in filtered if event.device_id == device_id]
        if event_type is not None:
            filtered = [event for event in filtered if event.event_type == event_type]
        if result is not None:
            filtered = [event for event in filtered if event.result == result]
        if start is not None:
            filtered = [event for event in filtered if event.created_at >= start]
        if end is not None:
            filtered = [event for event in filtered if event.created_at < end]
        return sorted(filtered, key=lambda event: event.created_at, reverse=True)[
            offset : offset + limit
        ]


def make_identity() -> VerifiedIdentity:
    user_id = uuid4()
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="events-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def create_use_case(
    identity: VerifiedIdentity,
    device_ids: set[UUID],
    project_ids: set[UUID],
    client_ids: set[UUID],
):
    events = EventRepositoryStub(client_ids)
    create = CreateEvent(
        events,
        DeviceRepositoryStub(device_ids),
        ProjectRepositoryStub(project_ids),
        NoOpUnitOfWork(),
    )
    return events, create


@pytest.mark.anyio
async def test_create_and_list_events_with_owner_scoped_filters() -> None:
    identity = make_identity()
    device_id, project_id, client_id = uuid4(), uuid4(), uuid4()
    events, create = create_use_case(identity, {device_id}, {project_id}, {client_id})
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    event_data = await create.create_event(
        identity,
        EventType.SERVICE_STARTED,
        EventResult.SUCCESS,
        created_at,
        project_id,
        device_id,
        "Service started",
        {"service": "api"},
        client_id,
    )

    result = await GetUserEvents(events).get_user_events(
        identity,
        project_id,
        device_id,
        EventType.SERVICE_STARTED,
        EventResult.SUCCESS,
        created_at,
        created_at + timedelta(minutes=1),
        100,
        0,
    )

    assert event_data.user_id == identity.user_id
    assert len(result) == 1
    assert result[0].metadata == {"service": "api"}


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("device_ids", "project_ids", "client_ids", "expected"),
    [
        ({}, set(), set(), DeviceNotFound),
        (set(), {}, set(), ProjectNotFound),
        (set(), set(), set(), EventClientDeviceNotFound),
    ],
)
async def test_create_event_rejects_unowned_references(
    device_ids, project_ids, client_ids, expected
) -> None:
    identity = make_identity()
    _, create = create_use_case(identity, device_ids, project_ids, client_ids)
    with pytest.raises(expected):
        await create.create_event(
            identity,
            EventType.OTHER,
            EventResult.INFORMATIONAL,
            datetime.now(UTC),
            uuid4() if expected is ProjectNotFound else None,
            uuid4() if expected is DeviceNotFound else None,
            None,
            None,
            uuid4() if expected is EventClientDeviceNotFound else None,
        )


@pytest.mark.anyio
async def test_create_event_rejects_secret_metadata_fields() -> None:
    identity = make_identity()
    _, create = create_use_case(identity, set(), set(), set())
    with pytest.raises(InvalidInput, match="must not contain secret"):
        await create.create_event(
            identity,
            EventType.OTHER,
            EventResult.INFORMATIONAL,
            datetime.now(UTC),
            None,
            None,
            None,
            {"nested": [{"api_key": "sensitive"}]},
            None,
        )
