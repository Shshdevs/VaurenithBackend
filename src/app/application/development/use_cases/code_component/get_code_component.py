from uuid import UUID

from app.application.development.dto import CodeComponentData
from app.application.development.exceptions import CodeComponentNotFound
from app.application.development.interfaces import CodeComponentRepository
from app.application.identity import VerifiedIdentity


class GetCodeComponent:
    def __init__(self, repository: CodeComponentRepository) -> None:
        self._repository = repository

    async def get_code_component(
        self, identity: VerifiedIdentity, component_id: UUID
    ) -> CodeComponentData:
        component = await self._repository.get_by_id(identity.user_id, component_id)
        if component is None:
            raise CodeComponentNotFound(str(component_id))
        return CodeComponentData.from_component(component)
