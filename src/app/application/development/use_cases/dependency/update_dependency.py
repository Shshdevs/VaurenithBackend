from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.application.common.exceptions import Conflict, InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.development.dto import DependencyData
from app.application.development.exceptions import (
    CodeComponentNotFound,
    DependencyNotFound,
)
from app.application.development.interfaces import (
    CodeComponentRepository,
    DependencyRepository,
)
from app.application.identity import VerifiedIdentity
from app.domain.common.enums import RelationOrigin
from app.domain.development.entities.dependency import Dependency
from app.domain.development.enums import DependencyType
from app.domain.development.exceptions import InvalidDependency


class UpdateDependency:
    def __init__(
        self,
        dependency_repository: DependencyRepository,
        component_repository: CodeComponentRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._dependencies = dependency_repository
        self._components = component_repository
        self._unit_of_work = unit_of_work

    @transactional
    async def update_dependency(
        self,
        identity: VerifiedIdentity,
        dependency_id: UUID,
        source_component_id: UUID,
        target_component_id: UUID,
        dependency_type: DependencyType,
        is_directed: bool,
        source_type: RelationOrigin,
        confidence: Decimal | None,
        analysis_version: str | None,
        analyzed_at: datetime | None,
        metadata: Any | None,
    ) -> DependencyData:
        existing = await self._dependencies.get_by_id(identity.user_id, dependency_id)
        if existing is None:
            raise DependencyNotFound(str(dependency_id))
        if await self._components.get_by_id(identity.user_id, source_component_id) is None:
            raise CodeComponentNotFound(str(source_component_id))
        if await self._components.get_by_id(identity.user_id, target_component_id) is None:
            raise CodeComponentNotFound(str(target_component_id))
        if not is_directed and target_component_id.int < source_component_id.int:
            source_component_id, target_component_id = (
                target_component_id,
                source_component_id,
            )
        try:
            dependency = Dependency(
                entity_id=existing.id,
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
        duplicate = await self._dependencies.get_by_key(
            identity.user_id,
            dependency.source_component_id,
            dependency.target_component_id,
            dependency.dependency_type,
        )
        if duplicate is not None and duplicate.id != dependency.id:
            raise Conflict("Dependency already exists between these components")
        if not await self._dependencies.update(identity.user_id, dependency):
            raise DependencyNotFound(str(dependency_id))
        return DependencyData.from_dependency(dependency)
