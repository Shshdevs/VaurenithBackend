from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.domain.development.entities.code_component import CodeComponent
from app.domain.development.entities.dependency import Dependency
from app.domain.development.enums import ComponentType


class CodeComponentRepositoryStub:
    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        self.components: dict[UUID, CodeComponent] = {}

    async def get_by_id(self, user_id: UUID, component_id: UUID):
        if user_id != self.user_id:
            return None
        return self.components.get(component_id)


class RepositoryRepositoryStub:
    def __init__(self, repository_ids: set[UUID]) -> None:
        self.repository_ids = repository_ids

    async def get_by_id(self, user_id: UUID, repository_id: UUID):
        return (
            SimpleNamespace(id=repository_id)
            if repository_id in self.repository_ids
            else None
        )


class DependencyRepositoryStub:
    def __init__(self, user_id: UUID, components: CodeComponentRepositoryStub) -> None:
        self.user_id = user_id
        self.components = components
        self.dependencies: dict[UUID, Dependency] = {}

    def _is_owned(self, user_id: UUID, dependency: Dependency) -> bool:
        return (
            user_id == self.user_id
            and dependency.source_component_id in self.components.components
            and dependency.target_component_id in self.components.components
        )

    async def get_by_id(self, user_id: UUID, dependency_id: UUID):
        dependency = self.dependencies.get(dependency_id)
        if dependency is None or not self._is_owned(user_id, dependency):
            return None
        return dependency

    async def get_by_component(self, user_id: UUID, component_id: UUID):
        if user_id != self.user_id or component_id not in self.components.components:
            return []
        return sorted(
            [
                dependency
                for dependency in self.dependencies.values()
                if self._is_owned(user_id, dependency)
                and component_id
                in {
                    dependency.source_component_id,
                    dependency.target_component_id,
                }
            ],
            key=lambda dependency: (
                dependency.dependency_type.value,
                dependency.source_component_id,
                dependency.target_component_id,
            ),
        )

    async def get_by_repository(self, user_id: UUID, repository_id: UUID):
        if user_id != self.user_id:
            return []
        return [
            dependency
            for dependency in self.dependencies.values()
            if self._is_owned(user_id, dependency)
            and any(
                self.components.components[component_id].repository_id == repository_id
                for component_id in (
                    dependency.source_component_id,
                    dependency.target_component_id,
                )
            )
        ]

    async def get_by_key(
        self,
        user_id: UUID,
        source_component_id: UUID,
        target_component_id: UUID,
        dependency_type,
    ):
        for dependency in self.dependencies.values():
            if (
                self._is_owned(user_id, dependency)
                and dependency.source_component_id == source_component_id
                and dependency.target_component_id == target_component_id
                and dependency.dependency_type == dependency_type
            ):
                return dependency
        return None

    async def create(self, user_id: UUID, dependency: Dependency) -> None:
        if not self._is_owned(user_id, dependency):
            raise ValueError("Code component not found")
        self.dependencies[dependency.id] = dependency

    async def update(self, user_id: UUID, dependency: Dependency) -> bool:
        existing = await self.get_by_id(user_id, dependency.id)
        if existing is None or not self._is_owned(user_id, dependency):
            return False
        self.dependencies[dependency.id] = dependency
        return True

    async def delete(self, user_id: UUID, dependency_id: UUID) -> bool:
        dependency = await self.get_by_id(user_id, dependency_id)
        if dependency is None:
            return False
        del self.dependencies[dependency_id]
        return True


def make_component(repository_id: UUID, **overrides) -> CodeComponent:
    now = datetime.now(UTC)
    values = {
        "entity_id": uuid4(),
        "repository_id": repository_id,
        "name": "module.py",
        "path": "src/module.py",
        "component_type": ComponentType.FILE,
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return CodeComponent(**values)
