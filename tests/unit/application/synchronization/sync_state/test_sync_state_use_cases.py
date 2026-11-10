from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.synchronization.exceptions import (
    SyncStateNotFound,
    SyncStateUpdateConflict,
    SyncStateVersionConflict,
)
from app.application.synchronization.use_cases.sync_state import (
    CreateSyncState,
    DeleteSyncState,
    GetSyncState,
    UpdateSyncState,
    UpdateSyncStatus,
)
from app.domain.common.enums import EntityType
from app.domain.identity import EmailAddress, TokenHash
from app.domain.synchronization import SyncState, SyncStatus


def make_identity() -> VerifiedIdentity:
    user_id = uuid4()
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="sync-state-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_sync_state(identity: VerifiedIdentity, **overrides: object) -> SyncState:
    values: dict[str, object] = {
        "sync_state_id": uuid4(),
        "user_id": identity.user_id,
        "client_device_id": uuid4(),
        "entity_type": EntityType.PROJECT,
        "entity_id": uuid4(),
        "updated_at": datetime.now(UTC),
        "local_version": 3,
        "server_version": 5,
        "status": SyncStatus.PENDING,
        "last_synced_at": datetime.now(UTC),
        "last_error": "previous error",
    }
    values.update(overrides)
    return SyncState(**values)  # type: ignore[arg-type]


class SyncStateRepositoryStub:
    def __init__(self) -> None:
        self.create_result = True
        self.update_result = True
        self.delete_result = True
        self.states: list[SyncState | None] = []
        self.created: list[SyncState] = []
        self.updated: list[tuple[int | None, SyncState]] = []
        self.expected_updated_at: list[datetime] = []
        self.deleted: list[tuple[object, object]] = []
        self.lookups: list[tuple[object, object]] = []

    async def create(self, sync_state: SyncState) -> bool:
        self.created.append(sync_state)
        return self.create_result

    async def update(
        self,
        user_id,
        sync_state: SyncState,
        expected_version: int | None,
        expected_updated_at: datetime,
    ) -> bool:
        self.updated.append((expected_version, sync_state))
        self.expected_updated_at.append(expected_updated_at)
        return self.update_result

    async def delete(self, user_id, sync_state_id) -> bool:
        self.deleted.append((user_id, sync_state_id))
        return self.delete_result

    async def get_sync_state(self, user_id, sync_state_id) -> SyncState | None:
        self.lookups.append((user_id, sync_state_id))
        if self.states:
            return self.states.pop(0)
        return None


@pytest.mark.anyio
async def test_create_sync_state_persists_state_for_authenticated_user() -> None:
    identity = make_identity()
    repository = SyncStateRepositoryStub()
    use_case = CreateSyncState(repository)
    client_device_id = uuid4()
    entity_id = uuid4()

    result = await use_case.execute(
        identity,
        client_device_id,
        EntityType.PROJECT,
        entity_id,
        local_version=2,
        server_version=4,
        status=SyncStatus.SYNCED,
    )

    state = repository.created[0]
    assert result.id == state.id
    assert state.user_id == identity.user_id
    assert state.client_device_id == client_device_id
    assert state.entity_type is EntityType.PROJECT
    assert state.entity_id == entity_id
    assert state.local_version == 2
    assert state.server_version == 4
    assert state.status is SyncStatus.SYNCED
    assert state.last_synced_at is not None


@pytest.mark.anyio
async def test_create_sync_state_rejects_invalid_domain_values() -> None:
    repository = SyncStateRepositoryStub()
    use_case = CreateSyncState(repository)

    with pytest.raises(InvalidInput):
        await use_case.execute(
            make_identity(),
            uuid4(),
            EntityType.PROJECT,
            uuid4(),
            local_version=-1,
            server_version=0,
            status=SyncStatus.PENDING,
        )

    assert repository.created == []


@pytest.mark.anyio
async def test_create_sync_state_rejects_device_not_owned_by_user() -> None:
    repository = SyncStateRepositoryStub()
    repository.create_result = False

    with pytest.raises(InvalidInput):
        await CreateSyncState(repository).execute(
            make_identity(),
            uuid4(),
            EntityType.PROJECT,
            uuid4(),
            local_version=0,
            server_version=0,
            status=SyncStatus.PENDING,
        )


@pytest.mark.anyio
async def test_create_sync_state_does_not_claim_unsynced_state_was_synced() -> None:
    repository = SyncStateRepositoryStub()

    result = await CreateSyncState(repository).execute(
        make_identity(),
        uuid4(),
        EntityType.PROJECT,
        uuid4(),
        local_version=0,
        server_version=0,
        status=SyncStatus.PENDING,
    )

    assert result.last_synced_at is None


@pytest.mark.anyio
async def test_create_sync_state_supports_device_cursor_without_entity_versions() -> None:
    identity = make_identity()
    repository = SyncStateRepositoryStub()

    result = await CreateSyncState(repository).execute(
        identity,
        uuid4(),
        entity_type=None,
        entity_id=None,
        local_version=None,
        server_version=None,
        status=SyncStatus.PENDING,
    )

    state = repository.created[0]
    assert result.entity_type is None
    assert result.entity_id is None
    assert result.local_version is None
    assert result.server_version is None
    assert state.user_id == identity.user_id


@pytest.mark.anyio
async def test_create_sync_state_rejects_only_one_entity_identifier() -> None:
    repository = SyncStateRepositoryStub()

    with pytest.raises(InvalidInput):
        await CreateSyncState(repository).execute(
            make_identity(),
            uuid4(),
            entity_type=EntityType.PROJECT,
            entity_id=None,
            local_version=None,
            server_version=None,
            status=SyncStatus.PENDING,
        )

    assert repository.created == []


@pytest.mark.anyio
async def test_get_sync_state_returns_data_and_scopes_lookup_to_user() -> None:
    identity = make_identity()
    state = make_sync_state(identity)
    repository = SyncStateRepositoryStub()
    repository.states = [state]

    result = await GetSyncState(repository).execute(identity, state.id)

    assert result.id == state.id
    assert result.user_id == identity.user_id
    assert repository.lookups == [(identity.user_id, state.id)]


@pytest.mark.anyio
async def test_get_sync_state_raises_when_state_is_missing() -> None:
    identity = make_identity()
    sync_state_id = uuid4()

    with pytest.raises(SyncStateNotFound):
        await GetSyncState(SyncStateRepositoryStub()).execute(identity, sync_state_id)


@pytest.mark.anyio
async def test_update_sync_state_increments_version_and_clears_last_error() -> None:
    identity = make_identity()
    existing = make_sync_state(identity)
    repository = SyncStateRepositoryStub()
    repository.states = [existing]

    result = await UpdateSyncState(repository).execute(
        existing.id,
        identity,
        expected_version=3,
        server_version=6,
        status=SyncStatus.SYNCED,
        last_error=None,
    )

    expected_version, updated = repository.updated[0]
    assert expected_version == 3
    assert updated.local_version == 4
    assert updated.server_version == 6
    assert updated.status is SyncStatus.SYNCED
    assert updated.client_device_id == existing.client_device_id
    assert updated.entity_type is existing.entity_type
    assert updated.entity_id == existing.entity_id
    assert updated.last_error is None
    assert updated.last_synced_at is not None
    assert result.local_version == 4
    assert repository.expected_updated_at == [existing.updated_at]


@pytest.mark.anyio
async def test_update_sync_state_rejects_stale_expected_version() -> None:
    identity = make_identity()
    existing = make_sync_state(identity, local_version=4)
    repository = SyncStateRepositoryStub()
    repository.states = [existing]

    with pytest.raises(SyncStateVersionConflict):
        await UpdateSyncState(repository).execute(
            existing.id,
            identity,
            expected_version=3,
            server_version=6,
            status=SyncStatus.SYNCED,
            last_error=None,
        )

    assert repository.updated == []


@pytest.mark.anyio
async def test_update_sync_state_preserves_last_synced_at_when_not_synced() -> None:
    identity = make_identity()
    existing = make_sync_state(identity, status=SyncStatus.SYNCED)
    repository = SyncStateRepositoryStub()
    repository.states = [existing]

    result = await UpdateSyncState(repository).execute(
        existing.id,
        identity,
        expected_version=3,
        server_version=6,
        status=SyncStatus.FAILED,
        last_error="network failure",
    )

    assert result.last_synced_at == existing.last_synced_at


@pytest.mark.anyio
async def test_update_sync_state_detects_race_after_version_check() -> None:
    identity = make_identity()
    existing = make_sync_state(identity)
    latest = make_sync_state(
        identity,
        sync_state_id=existing.id,
        local_version=4,
        updated_at=existing.updated_at + timedelta(seconds=1),
    )
    repository = SyncStateRepositoryStub()
    repository.states = [existing, latest]
    repository.update_result = False

    with pytest.raises(SyncStateVersionConflict) as error:
        await UpdateSyncState(repository).execute(
            existing.id,
            identity,
            expected_version=3,
            server_version=6,
            status=SyncStatus.SYNCED,
            last_error=None,
        )

    assert "current version is 4" in str(error.value)


@pytest.mark.anyio
async def test_update_sync_state_detects_deletion_during_update() -> None:
    identity = make_identity()
    existing = make_sync_state(identity)
    repository = SyncStateRepositoryStub()
    repository.states = [existing, None]
    repository.update_result = False

    with pytest.raises(SyncStateNotFound):
        await UpdateSyncState(repository).execute(
            existing.id,
            identity,
            expected_version=3,
            server_version=6,
            status=SyncStatus.SYNCED,
            last_error=None,
        )


@pytest.mark.anyio
async def test_update_sync_status_changes_status_without_changing_versions() -> None:
    identity = make_identity()
    existing = make_sync_state(identity)
    repository = SyncStateRepositoryStub()
    repository.states = [existing]

    result = await UpdateSyncStatus(repository).execute(
        existing.id,
        identity,
        SyncStatus.FAILED,
    )

    expected_version, updated = repository.updated[0]
    assert expected_version == existing.local_version
    assert updated.local_version == existing.local_version
    assert updated.server_version == existing.server_version
    assert updated.status is SyncStatus.FAILED
    assert updated.last_synced_at == existing.last_synced_at
    assert result.sync_status is SyncStatus.FAILED
    assert repository.expected_updated_at == [existing.updated_at]


@pytest.mark.anyio
async def test_update_sync_status_raises_version_conflict_after_concurrent_update() -> None:
    identity = make_identity()
    existing = make_sync_state(identity)
    latest = make_sync_state(
        identity,
        sync_state_id=existing.id,
        local_version=existing.local_version,
        updated_at=existing.updated_at + timedelta(seconds=1),
    )
    repository = SyncStateRepositoryStub()
    repository.states = [existing, latest]
    repository.update_result = False

    with pytest.raises(SyncStateUpdateConflict):
        await UpdateSyncStatus(repository).execute(
            existing.id,
            identity,
            SyncStatus.FAILED,
        )


@pytest.mark.anyio
async def test_update_sync_status_raises_not_found_when_state_is_deleted() -> None:
    identity = make_identity()
    existing = make_sync_state(identity)
    repository = SyncStateRepositoryStub()
    repository.states = [existing, None]
    repository.update_result = False

    with pytest.raises(SyncStateNotFound):
        await UpdateSyncStatus(repository).execute(
            existing.id,
            identity,
            SyncStatus.FAILED,
        )


@pytest.mark.anyio
async def test_delete_sync_state_deletes_state_for_authenticated_user() -> None:
    identity = make_identity()
    existing = make_sync_state(identity)
    repository = SyncStateRepositoryStub()
    repository.states = [existing]

    await DeleteSyncState(repository).execute(identity, existing.id)

    assert repository.deleted == [(identity.user_id, existing.id)]


@pytest.mark.anyio
async def test_delete_sync_state_raises_when_state_is_missing() -> None:
    identity = make_identity()
    sync_state_id = uuid4()

    with pytest.raises(SyncStateNotFound):
        await DeleteSyncState(SyncStateRepositoryStub()).execute(identity, sync_state_id)


@pytest.mark.anyio
async def test_delete_sync_state_raises_if_delete_reports_missing_state() -> None:
    identity = make_identity()
    existing = make_sync_state(identity)
    repository = SyncStateRepositoryStub()
    repository.states = [existing]
    repository.delete_result = False

    with pytest.raises(SyncStateNotFound):
        await DeleteSyncState(repository).execute(identity, existing.id)
