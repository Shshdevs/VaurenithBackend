from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from tests.support import NoOpUnitOfWork
from tests.unit.application.development.dependency.conftest import (
    CodeComponentRepositoryStub,
    DependencyRepositoryStub,
    RepositoryRepositoryStub,
    make_component,
)

from app.application.common.exceptions import Conflict, InvalidInput
from app.application.development import (
    CodeComponentNotFound,
    CreateDependency,
    DeleteDependency,
    DependencyNotFound,
    GetComponentDependencies,
    GetDependency,
    GetRepositoryDependencies,
    RepositoryNotFound,
    UpdateDependency,
)
from app.application.identity import VerifiedIdentity
from app.domain.common.enums import RelationOrigin
from app.domain.development.enums import DependencyType
from app.domain.identity import EmailAddress, TokenHash


def make_identity() -> VerifiedIdentity:
    user_id = uuid4()
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="dependency-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_use_cases(identity: VerifiedIdentity, repository_ids: set):
    components = CodeComponentRepositoryStub(identity.user_id)
    repositories = RepositoryRepositoryStub(repository_ids)
    dependencies = DependencyRepositoryStub(identity.user_id, components)
    unit_of_work = NoOpUnitOfWork()
    return (
        components,
        dependencies,
        CreateDependency(dependencies, components, repositories, unit_of_work),
        GetDependency(dependencies),
        GetComponentDependencies(dependencies, components),
        GetRepositoryDependencies(dependencies, repositories),
        UpdateDependency(dependencies, components, unit_of_work),
        DeleteDependency(dependencies, unit_of_work),
    )


@pytest.mark.anyio
async def test_dependency_lifecycle_and_incident_queries() -> None:
    identity = make_identity()
    repository_id = uuid4()
    components, dependencies, create, get, get_component, get_repository, update, delete = (
        make_use_cases(identity, {repository_id})
    )
    source = make_component(repository_id, name="source.py", path="src/source.py")
    target = make_component(repository_id, name="target.py", path="src/target.py")
    components.components[source.id] = source
    components.components[target.id] = target

    created = await create.create_dependency(
        identity,
        repository_id,
        source.id,
        target.id,
        DependencyType.IMPORT,
        source_type=RelationOrigin.USER_DEFINED,
        confidence=Decimal("0.8750"),
        analysis_version="1.0",
        analyzed_at=datetime.now(UTC),
        metadata={"module": "target"},
    )

    assert created.source_component_id == source.id
    assert created.target_component_id == target.id
    assert created.confidence == Decimal("0.8750")
    assert await get.get_dependency(identity, created.id) == created
    assert await get_component.get_component_dependencies(identity, source.id) == [created]
    assert await get_component.get_component_dependencies(identity, target.id) == [created]
    assert await get_repository.get_repository_dependencies(identity, repository_id) == [
        created
    ]

    updated = await update.update_dependency(
        identity,
        created.id,
        target.id,
        source.id,
        DependencyType.REFERENCE,
        False,
        RelationOrigin.USER_DEFINED,
        Decimal("1.0000"),
        "1.1",
        datetime.now(UTC),
        {"reviewed": True},
    )
    assert updated.dependency_type is DependencyType.REFERENCE
    expected_source_id, expected_target_id = sorted(
        (source.id, target.id), key=lambda component_id: component_id.int
    )
    assert updated.source_component_id == expected_source_id
    assert updated.target_component_id == expected_target_id
    assert not updated.is_directed
    assert updated.metadata == {"reviewed": True}

    await delete.delete_dependency(identity, created.id)
    with pytest.raises(DependencyNotFound):
        await get.get_dependency(identity, created.id)
    assert dependencies.dependencies == {}


@pytest.mark.anyio
async def test_dependency_validates_ownership_confidence_and_unique_edge() -> None:
    identity = make_identity()
    repository_id = uuid4()
    components, _, create, _, _, _, _, _ = make_use_cases(identity, {repository_id})
    source = make_component(repository_id)
    target = make_component(repository_id)
    components.components[source.id] = source
    components.components[target.id] = target

    with pytest.raises(RepositoryNotFound):
        await create.create_dependency(
            identity,
            uuid4(),
            source.id,
            target.id,
            DependencyType.IMPORT,
        )
    with pytest.raises(CodeComponentNotFound):
        await create.create_dependency(
            identity,
            repository_id,
            source.id,
            uuid4(),
            DependencyType.IMPORT,
        )
    with pytest.raises(InvalidInput):
        await create.create_dependency(
            identity,
            repository_id,
            source.id,
            target.id,
            DependencyType.IMPORT,
            confidence=Decimal("1.0001"),
        )

    await create.create_dependency(
        identity,
        repository_id,
        source.id,
        target.id,
        DependencyType.IMPORT,
        is_directed=False,
    )
    with pytest.raises(Conflict):
        await create.create_dependency(
            identity,
            repository_id,
            target.id,
            source.id,
            DependencyType.IMPORT,
            is_directed=False,
        )


@pytest.mark.anyio
async def test_dependency_rejects_foreign_components_and_unrelated_repository() -> None:
    identity = make_identity()
    repository_id = uuid4()
    other_repository_id = uuid4()
    unrelated_repository_id = uuid4()
    components, dependencies, create, get, get_component, get_repository, update, delete = (
        make_use_cases(
            identity, {repository_id, other_repository_id, unrelated_repository_id}
        )
    )
    source = make_component(repository_id)
    other = make_component(other_repository_id)
    components.components[source.id] = source
    components.components[other.id] = other

    with pytest.raises(InvalidInput):
        await create.create_dependency(
            identity,
            unrelated_repository_id,
            source.id,
            other.id,
            DependencyType.CALL,
        )
    cross_repository = await create.create_dependency(
        identity,
        repository_id,
        source.id,
        other.id,
        DependencyType.CALL,
    )
    assert await get_repository.get_repository_dependencies(
        identity, other_repository_id
    ) == [cross_repository]

    other_identity = make_identity()
    _, _, _, other_get, other_component_dependencies, _, other_update, other_delete = (
        make_use_cases(other_identity, {repository_id, other_repository_id})
    )
    with pytest.raises(DependencyNotFound):
        await other_get.get_dependency(other_identity, cross_repository.id)
    with pytest.raises(CodeComponentNotFound):
        await other_component_dependencies.get_component_dependencies(
            other_identity, source.id
        )
    with pytest.raises(DependencyNotFound):
        await other_update.update_dependency(
            other_identity,
            cross_repository.id,
            source.id,
            other.id,
            DependencyType.CALL,
            True,
            RelationOrigin.AUTOMATIC,
            None,
            None,
            None,
            None,
        )
    with pytest.raises(DependencyNotFound):
        await other_delete.delete_dependency(other_identity, cross_repository.id)
    assert dependencies.dependencies
