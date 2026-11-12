from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.development.dto import CodeComponentData
from app.application.development.dto.code_component_change_data import (
    code_component_change_data,
)
from app.application.development.exceptions import RepositoryNotFound
from app.application.development.interfaces import (
    CodeComponentRepository,
    RepositoryRepository,
)
from app.application.identity import VerifiedIdentity
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.development.entities.code_component import CodeComponent
from app.domain.development.enums import ComponentType
from app.domain.development.exceptions import InvalidCodeComponent
from app.domain.synchronization import ChangeOperation


class CreateCodeComponent:
    def __init__(
        self,
        component_repository: CodeComponentRepository,
        repository_repository: RepositoryRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._components = component_repository
        self._repositories = repository_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def create_code_component(
        self,
        identity: VerifiedIdentity,
        repository_id: UUID,
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
        if await self._repositories.get_by_id(identity.user_id, repository_id) is None:
            raise RepositoryNotFound(str(repository_id))
        now = datetime.now(UTC)
        try:
            component = CodeComponent(
                entity_id=uuid4(),
                repository_id=repository_id,
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
                created_at=now,
                updated_at=now,
            )
        except (InvalidCodeComponent, ValueError) as error:
            raise InvalidInput(str(error)) from error
        try:
            await self._components.create(identity.user_id, component)
        except ValueError as error:
            raise InvalidInput(str(error)) from error
        await self._record(identity, component, ChangeOperation.INSERT)
        return CodeComponentData.from_component(component)

    async def _record(self, identity, component, operation) -> None:
        await self._recorder.execute(
            identity,
            EntityType.CODE_COMPONENT,
            component.id,
            operation,
            1,
            code_component_change_data(component),
        )
