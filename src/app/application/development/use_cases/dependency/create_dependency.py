from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from app.application.common.exceptions import Conflict, InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.development.dto import DependencyData
from app.application.development.exceptions import (
    CodeComponentNotFound,
    RepositoryNotFound,
)
from app.application.development.interfaces import (
    CodeComponentRepository,
    DependencyRepository,
    RepositoryRepository,
)
from app.application.identity import VerifiedIdentity
from app.domain.common.enums import RelationOrigin
from app.domain.development.entities.dependency import Dependency
from app.domain.development.enums import DependencyType
from app.domain.development.exceptions import InvalidDependency


class CreateDependency:
    def __init__(
        self,
        dependency_repository: DependencyRepository,
        component_repository: CodeComponentRepository,
        repository_repository: RepositoryRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._dependencies = dependency_repository
        self._components = component_repository
        self._repositories = repository_repository
        self._unit_of_work = unit_of_work

    @transactional
    async def create_dependency(
        self,
        identity: VerifiedIdentity,
        repository_id: UUID,
        source_component_id: UUID,
        target_component_id: UUID,
        dependency_type: DependencyType,
        is_directed: bool = True,
        source_type: RelationOrigin = RelationOrigin.AUTOMATIC,
        confidence: Decimal | None = None,
        analysis_version: str | None = None,
        analyzed_at: datetime | None = None,
        metadata: Any | None = None,
    ) -> DependencyData:
        if await self._repositories.get_by_id(identity.user_id, repository_id) is None:
            raise RepositoryNotFound(str(repository_id))
        source = await self._components.get_by_id(identity.user_id, source_component_id)
        target = await self._components.get_by_id(identity.user_id, target_component_id)
        if source is None:
            raise CodeComponentNotFound(str(source_component_id))
        if target is None:
            raise CodeComponentNotFound(str(target_component_id))
        if repository_id not in {source.repository_id, target.repository_id}:
            raise InvalidInput(
                "At least one dependency component must belong to the repository"
            )
        if not is_directed and target_component_id.int < source_component_id.int:
            source_component_id, target_component_id = (
                target_component_id,
                source_component_id,
            )
        try:
            dependency = Dependency(
                entity_id=uuid4(),
                source_component_id=source_component_id,
                target_component_id=target_component_id,
                dependency_type=DependencyType(dependency_type),
                is_directed=is_directed,
                source_type=RelationOrigin(source_type),
                confidence=confidence,
                analysis_version=analysis_version,
                analyzed_at=analyzed_at,
                metadata=metadata,
            )
        except (InvalidDependency, ValueError) as error:
            raise InvalidInput(str(error)) from error
        if await self._dependencies.get_by_key(
            identity.user_id,
            dependency.source_component_id,
            dependency.target_component_id,
            dependency.dependency_type,
        ):
            raise Conflict("Dependency already exists between these components")
        try:
            await self._dependencies.create(identity.user_id, dependency)
        except ValueError as error:
            raise InvalidInput(str(error)) from error
        return DependencyData.from_dependency(dependency)
