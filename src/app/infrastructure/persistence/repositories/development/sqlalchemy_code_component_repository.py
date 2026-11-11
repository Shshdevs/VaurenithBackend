from uuid import UUID

from sqlalchemy import delete, exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Exists

from app.application.development.interfaces import CodeComponentRepository
from app.domain.development.entities.code_component import (
    CodeComponent as CodeComponentEntity,
)
from app.infrastructure.persistence.models.development.code_component import (
    CodeComponent,
)
from app.infrastructure.persistence.models.development.dependency import Dependency
from app.infrastructure.persistence.models.development.repository import Repository
from app.infrastructure.persistence.models.projects.project import Project


class SqlAlchemyCodeComponentRepository(CodeComponentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, user_id: UUID, component_id: UUID
    ) -> CodeComponentEntity | None:
        result = await self._session.execute(
            select(CodeComponent)
            .join(Repository, Repository.id == CodeComponent.repository_id)
            .where(
                CodeComponent.id == component_id,
                self._owned_repository(user_id),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def get_by_repository(
        self, user_id: UUID, repository_id: UUID
    ) -> list[CodeComponentEntity]:
        result = await self._session.execute(
            select(CodeComponent)
            .join(Repository, Repository.id == CodeComponent.repository_id)
            .where(
                CodeComponent.repository_id == repository_id,
                self._owned_repository(user_id),
            )
            .order_by(CodeComponent.path, CodeComponent.symbol, CodeComponent.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def create(self, user_id: UUID, component: CodeComponentEntity) -> None:
        if not await self._repository_is_owned(user_id, component.repository_id):
            raise ValueError("Repository not found")
        if component.parent_id is not None:
            parent = await self._session.scalar(
                select(CodeComponent.id).where(
                    CodeComponent.id == component.parent_id,
                    CodeComponent.repository_id == component.repository_id,
                )
            )
            if parent is None:
                raise ValueError("Parent component not found in repository")
        self._session.add(self._to_model(component))

    async def update(
        self, user_id: UUID, component: CodeComponentEntity, expected_version: int
    ) -> bool:
        if component.parent_id == component.id:
            raise ValueError("A code component cannot be its own parent")
        if component.parent_id is not None:
            parent = await self._session.scalar(
                select(CodeComponent.id).where(
                    CodeComponent.id == component.parent_id,
                    CodeComponent.repository_id == component.repository_id,
                )
            )
            if parent is None:
                raise ValueError("Parent component not found in repository")
            ancestors = (
                select(CodeComponent.id, CodeComponent.parent_id)
                .where(
                    CodeComponent.id == component.parent_id,
                    CodeComponent.repository_id == component.repository_id,
                )
                .cte("component_ancestors", recursive=True)
            )
            ancestors = ancestors.union_all(
                select(CodeComponent.id, CodeComponent.parent_id).join(
                    ancestors, CodeComponent.id == ancestors.c.parent_id
                )
            )
            creates_cycle = await self._session.scalar(
                select(exists().where(ancestors.c.id == component.id))
            )
            if creates_cycle:
                raise ValueError("Parent component cannot be a descendant")
        result = await self._session.execute(
            update(CodeComponent)
            .where(
                CodeComponent.id == component.id,
                CodeComponent.repository_id == component.repository_id,
                CodeComponent.version == expected_version,
                self._owned_repository(user_id),
            )
            .values(
                parent_id=component.parent_id,
                name=component.name,
                path=component.path,
                component_type=component.component_type,
                language=component.language,
                symbol=component.symbol,
                start_line=component.start_line,
                end_line=component.end_line,
                analysis_version=component.analysis_version,
                analyzed_at=component.analyzed_at,
                source_commit_hash=component.source_commit_hash,
                updated_at=component.updated_at,
                version=component.version,
            )
            .returning(CodeComponent.id)
        )
        return result.scalar_one_or_none() is not None

    async def delete(
        self, user_id: UUID, component_id: UUID, expected_version: int
    ) -> bool:
        component = await self._session.scalar(
            select(CodeComponent)
            .join(Repository, Repository.id == CodeComponent.repository_id)
            .where(CodeComponent.id == component_id, self._owned_repository(user_id))
        )
        if component is None or component.version != expected_version:
            return False
        references = await self._session.scalar(
            select(Dependency.id)
            .where(
                (Dependency.source_component_id == component_id)
                | (Dependency.target_component_id == component_id)
            )
            .limit(1)
        )
        children = await self._session.scalar(
            select(CodeComponent.id).where(CodeComponent.parent_id == component_id).limit(1)
        )
        if references is not None or children is not None:
            raise ValueError("Code component is referenced by another component")
        result = await self._session.execute(
            delete(CodeComponent)
            .where(
                CodeComponent.id == component_id,
                CodeComponent.version == expected_version,
                self._owned_repository(user_id),
            )
            .returning(CodeComponent.id)
        )
        return result.scalar_one_or_none() is not None

    async def _repository_is_owned(self, user_id: UUID, repository_id: UUID) -> bool:
        return bool(
            await self._session.scalar(
                select(
                    exists().where(
                        Repository.id == repository_id,
                        self._owned_repository(user_id),
                    )
                )
            )
        )

    @staticmethod
    def _owned_repository(user_id: UUID) -> Exists:
        return exists(
            select(Project.id).where(
                Project.id == Repository.project_id,
                Project.user_id == user_id,
                Project.deleted_at.is_(None),
                Repository.deleted_at.is_(None),
            )
        )

    @staticmethod
    def _to_entity(model: CodeComponent) -> CodeComponentEntity:
        return CodeComponentEntity(
            entity_id=model.id,
            repository_id=model.repository_id,
            parent_id=model.parent_id,
            name=model.name,
            path=model.path,
            component_type=model.component_type,
            language=model.language,
            symbol=model.symbol,
            start_line=model.start_line,
            end_line=model.end_line,
            analysis_version=model.analysis_version,
            analyzed_at=model.analyzed_at,
            source_commit_hash=model.source_commit_hash,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )

    @staticmethod
    def _to_model(entity: CodeComponentEntity) -> CodeComponent:
        return CodeComponent(
            id=entity.id,
            repository_id=entity.repository_id,
            parent_id=entity.parent_id,
            name=entity.name,
            path=entity.path,
            component_type=entity.component_type,
            language=entity.language,
            symbol=entity.symbol,
            start_line=entity.start_line,
            end_line=entity.end_line,
            analysis_version=entity.analysis_version,
            analyzed_at=entity.analyzed_at,
            source_commit_hash=entity.source_commit_hash,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            version=entity.version,
        )
