from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.domain.development import CodeComponent, ComponentType


class CodeComponentRepositoryStub:
    def __init__(self, user_id: UUID, repository_ids: set[UUID]) -> None:
        self.user_id = user_id
        self.repository_ids = repository_ids
        self.components: dict[UUID, CodeComponent] = {}
        self.referenced_components: set[UUID] = set()

    async def get_by_id(self, user_id: UUID, component_id: UUID):
        if user_id != self.user_id:
            return None
        component = self.components.get(component_id)
        if component is None or component.repository_id not in self.repository_ids:
            return None
        return component

    async def get_by_repository(self, user_id: UUID, repository_id: UUID):
        if user_id != self.user_id or repository_id not in self.repository_ids:
            return []
        return [
            component
            for component in self.components.values()
            if component.repository_id == repository_id
        ]

    async def create(self, user_id: UUID, component: CodeComponent) -> None:
        if user_id != self.user_id or component.repository_id not in self.repository_ids:
            raise ValueError("Repository not found")
        if component.parent_id is not None:
            parent = self.components.get(component.parent_id)
            if parent is None or parent.repository_id != component.repository_id:
                raise ValueError("Parent component not found in repository")
        self.components[component.id] = component

    async def update(self, user_id: UUID, component: CodeComponent, expected_version: int):
        existing = await self.get_by_id(user_id, component.id)
        if existing is None or existing.version != expected_version:
            return False
        if component.parent_id is not None:
            parent = self.components.get(component.parent_id)
            if parent is None or parent.repository_id != component.repository_id:
                raise ValueError("Parent component not found in repository")
            if self._is_descendant(component.parent_id, component.id):
                raise ValueError("Parent component cannot be a descendant")
        self.components[component.id] = component
        return True

    async def delete(self, user_id: UUID, component_id: UUID, expected_version: int):
        component = await self.get_by_id(user_id, component_id)
        if component is None or component.version != expected_version:
            return False
        if component_id in self.referenced_components or any(
            item.parent_id == component_id for item in self.components.values()
        ):
            raise ValueError("Code component is referenced by another component")
        del self.components[component_id]
        return True

    def _is_descendant(self, component_id: UUID, candidate_id: UUID) -> bool:
        component = self.components.get(component_id)
        while component is not None and component.parent_id is not None:
            if component.parent_id == candidate_id:
                return True
            component = self.components.get(component.parent_id)
        return False


class RepositoryRepositoryStub:
    def __init__(self, repository_ids: set[UUID]) -> None:
        self.repository_ids = repository_ids

    async def get_by_id(self, user_id: UUID, repository_id: UUID):
        return (
            SimpleNamespace(id=repository_id)
            if repository_id in self.repository_ids
            else None
        )


class ChangeRecorderStub:
    def __init__(self) -> None:
        self.records: list[tuple] = []

    async def execute(self, *args) -> None:
        self.records.append(args)


def make_component(repository_id: UUID, **overrides) -> CodeComponent:
    now = datetime.now(UTC)
    values = {
        "entity_id": uuid4(),
        "repository_id": repository_id,
        "name": "main.py",
        "path": "src/main.py",
        "component_type": ComponentType.FILE,
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return CodeComponent(**values)
