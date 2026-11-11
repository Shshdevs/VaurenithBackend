from datetime import UTC, datetime
from uuid import UUID

from app.application.common.exceptions import Conflict, InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.development.dto import CodeComponentData
from app.application.development.dto.code_component_change_data import (
    code_component_change_data,
)
from app.application.development.exceptions import (
    CodeComponentNotFound,
    CodeComponentVersionConflict,
)
from app.application.development.interfaces import CodeComponentRepository
from app.application.identity import VerifiedIdentity
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.development.entities.code_component import CodeComponent
from app.domain.development.enums import ComponentType
from app.domain.development.exceptions import InvalidCodeComponent
from app.domain.synchronization import ChangeOperation


class UpdateCodeComponent:
    def __init__(
        self,
        repository: CodeComponentRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def update_code_component(
        self,
        identity: VerifiedIdentity,
        component_id: UUID,
        expected_version: int,
        name: str,
        path: str,
        component_type: ComponentType,
        parent_id: UUID | None = None,
        language: str | None = None,
        symbol: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        analysis_version: str | None = None,
        analyzed_at: datetime | None = None,
        source_commit_hash: str | None = None,
    ) -> CodeComponentData:
        existing = await self._repository.get_by_id(identity.user_id, component_id)
        if existing is None:
            raise CodeComponentNotFound(str(component_id))
        if existing.version != expected_version:
            raise CodeComponentVersionConflict(expected_version)
        try:
            component = CodeComponent(
                entity_id=existing.id,
                repository_id=existing.repository_id,
                parent_id=parent_id,
                name=name,
                path=path,
                component_type=ComponentType(component_type),
                language=language,
                symbol=symbol,
                start_line=start_line,
                end_line=end_line,
                analysis_version=analysis_version,
                analyzed_at=analyzed_at,
                source_commit_hash=source_commit_hash,
                created_at=existing.created_at,
                updated_at=datetime.now(UTC),
                version=expected_version + 1,
            )
        except (InvalidCodeComponent, ValueError) as error:
            raise InvalidInput(str(error)) from error
        try:
            if not await self._repository.update(
                identity.user_id, component, expected_version
            ):
                raise CodeComponentVersionConflict(expected_version)
        except ValueError as error:
            raise Conflict(str(error)) from error
        await self._recorder.execute(
            identity,
            EntityType.CODE_COMPONENT,
            component.id,
            ChangeOperation.UPDATE,
            component.version,
            code_component_change_data(component),
        )
        return CodeComponentData.from_component(component)
