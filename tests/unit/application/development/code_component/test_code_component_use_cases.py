from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from tests.support import NoOpUnitOfWork
from tests.unit.application.development.code_component.conftest import (
    ChangeRecorderStub,
    CodeComponentRepositoryStub,
    RepositoryRepositoryStub,
    make_component,
)

from app.application.common.exceptions import Conflict, InvalidInput
from app.application.development import (
    CodeComponentNotFound,
    CodeComponentVersionConflict,
    CreateCodeComponent,
    DeleteCodeComponent,
    GetCodeComponent,
    GetRepositoryCodeComponents,
    RepositoryNotFound,
    UpdateCodeComponent,
)
from app.application.identity import VerifiedIdentity
from app.domain.common.enums import EntityType
from app.domain.development import ComponentType
from app.domain.identity import EmailAddress, TokenHash
from app.domain.synchronization import ChangeOperation


def make_identity():
    user_id = uuid4()
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="code-component-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_use_cases(identity: VerifiedIdentity, repository_id):
    repository_ids = {repository_id}
    components = CodeComponentRepositoryStub(identity.user_id, repository_ids)
    repositories = RepositoryRepositoryStub(repository_ids)
    recorder = ChangeRecorderStub()
    unit_of_work = NoOpUnitOfWork()
    return (
        components,
        recorder,
        CreateCodeComponent(components, repositories, recorder, unit_of_work),
        GetCodeComponent(components),
        GetRepositoryCodeComponents(components, repositories),
        UpdateCodeComponent(components, recorder, unit_of_work),
        DeleteCodeComponent(components, recorder, unit_of_work),
    )


async def create_component(use_case, identity, repository_id, **values):
    return await use_case.create_code_component(
        identity,
        repository_id,
        values.pop("name", "main.py"),
        values.pop("path", "src/main.py"),
        values.pop("component_type", ComponentType.FILE),
        **values,
    )


@pytest.mark.anyio
async def test_code_component_lifecycle_versions_and_change_log() -> None:
    identity = make_identity()
    repository_id = uuid4()
    components, recorder, create, get, list_components, update, delete = make_use_cases(
        identity, repository_id
    )

    created = await create_component(
        create,
        identity,
        repository_id,
        language="python",
        symbol="main",
        start_line=1,
        end_line=20,
        analysis_version="1.0",
    )
    fetched = await get.get_code_component(identity, created.id)
    listed = await list_components.get_repository_code_components(identity, repository_id)
    updated = await update.update_code_component(
        identity,
        created.id,
        created.version,
        "app.py",
        "src/app.py",
        ComponentType.FILE,
        language="python",
        symbol="app",
        start_line=1,
        end_line=30,
        analysis_version="1.1",
        analyzed_at=datetime.now(UTC),
        source_commit_hash="a" * 40,
    )

    assert fetched == created
    assert listed == [created]
    assert updated.version == 2
    assert updated.name == "app.py"
    assert [record[3:5] for record in recorder.records] == [
        (ChangeOperation.INSERT, 1),
        (ChangeOperation.UPDATE, 2),
    ]
    assert recorder.records[0][1] is EntityType.CODE_COMPONENT

    with pytest.raises(CodeComponentVersionConflict):
        await update.update_code_component(
            identity, created.id, 1, "stale.py", "stale.py", ComponentType.FILE
        )

    await delete.delete_code_component(identity, created.id, 2)
    assert created.id not in components.components
    assert recorder.records[-1][3:5] == (ChangeOperation.DELETE, 3)
    with pytest.raises(CodeComponentNotFound):
        await get.get_code_component(identity, created.id)


@pytest.mark.anyio
async def test_code_component_scopes_access_and_validates_repository_and_parent() -> None:
    identity = make_identity()
    repository_id = uuid4()
    _, _, create, get, list_components, _, _ = make_use_cases(identity, repository_id)
    foreign_repository_id = uuid4()

    with pytest.raises(RepositoryNotFound):
        await create_component(create, identity, foreign_repository_id)
    with pytest.raises(InvalidInput):
        await create_component(
            create,
            identity,
            repository_id,
            parent_id=uuid4(),
        )

    component = make_component(repository_id)
    other_identity = make_identity()
    components, _, _, other_get, _, _, _ = make_use_cases(
        other_identity, foreign_repository_id
    )
    components.components[component.id] = component
    with pytest.raises(CodeComponentNotFound):
        await other_get.get_code_component(other_identity, component.id)
    with pytest.raises(RepositoryNotFound):
        await list_components.get_repository_code_components(
            identity, foreign_repository_id
        )


@pytest.mark.anyio
async def test_code_component_delete_rejects_referenced_component() -> None:
    identity = make_identity()
    repository_id = uuid4()
    components, _, _, _, _, _, delete = make_use_cases(identity, repository_id)
    component = make_component(repository_id)
    components.components[component.id] = component
    components.referenced_components.add(component.id)

    with pytest.raises(Conflict):
        await delete.delete_code_component(identity, component.id, component.version)

    assert component.id in components.components
