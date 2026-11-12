from uuid import UUID

from sqlalchemy import delete, exists, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.selectable import Exists

from app.application.development.interfaces import DependencyRepository
from app.domain.development.entities.dependency import Dependency as DependencyEntity
from app.domain.development.enums import DependencyType
from app.infrastructure.persistence.models.development.code_component import CodeComponent
from app.infrastructure.persistence.models.development.dependency import Dependency
from app.infrastructure.persistence.models.development.repository import Repository
from app.infrastructure.persistence.models.projects.project import Project


class SqlAlchemyDependencyRepository(DependencyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, user_id: UUID, dependency_id: UUID
    ) -> DependencyEntity | None:
        result = await self._session.execute(
            select(Dependency).where(
                Dependency.id == dependency_id,
                self._owned_dependency(user_id),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def get_by_component(
        self, user_id: UUID, component_id: UUID
    ) -> list[DependencyEntity]:
        result = await self._session.execute(
            select(Dependency)
            .where(
                or_(
                    Dependency.source_component_id == component_id,
                    Dependency.target_component_id == component_id,
                ),
                self._owned_dependency(user_id),
            )
            .order_by(
                Dependency.dependency_type,
                Dependency.source_component_id,
                Dependency.target_component_id,
                Dependency.id,
            )
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_repository(
        self, user_id: UUID, repository_id: UUID
    ) -> list[DependencyEntity]:
        source = aliased(CodeComponent)
        target = aliased(CodeComponent)
        source_in_repository = exists(
            select(source.id).where(
                source.id == Dependency.source_component_id,
                source.repository_id == repository_id,
            )
        )
        target_in_repository = exists(
            select(target.id).where(
                target.id == Dependency.target_component_id,
                target.repository_id == repository_id,
            )
        )
        result = await self._session.execute(
            select(Dependency)
            .where(
                or_(source_in_repository, target_in_repository),
                self._owned_dependency(user_id),
            )
            .order_by(
                Dependency.dependency_type,
                Dependency.source_component_id,
                Dependency.target_component_id,
                Dependency.id,
            )
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_key(
        self,
        user_id: UUID,
        source_component_id: UUID,
        target_component_id: UUID,
        dependency_type: DependencyType,
    ) -> DependencyEntity | None:
        result = await self._session.execute(
            select(Dependency).where(
                Dependency.source_component_id == source_component_id,
                Dependency.target_component_id == target_component_id,
                Dependency.dependency_type == dependency_type,
                self._owned_dependency(user_id),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def create(self, user_id: UUID, dependency: DependencyEntity) -> None:
        if not await self._components_are_owned(
            user_id,
            dependency.source_component_id,
            dependency.target_component_id,
        ):
            raise ValueError("Code component not found")
        self._session.add(self._to_model(dependency))

    async def update(self, user_id: UUID, dependency: DependencyEntity) -> bool:
        if not await self._components_are_owned(
            user_id,
            dependency.source_component_id,
            dependency.target_component_id,
        ):
            raise ValueError("Code component not found")
        result = await self._session.execute(
            update(Dependency)
            .where(
                Dependency.id == dependency.id,
                self._owned_dependency(user_id),
            )
            .values(
                source_component_id=dependency.source_component_id,
                target_component_id=dependency.target_component_id,
                dependency_type=dependency.dependency_type,
                is_directed=dependency.is_directed,
                source_type=dependency.source_type,
                confidence=dependency.confidence,
                analysis_version=dependency.analysis_version,
                analyzed_at=dependency.analyzed_at,
                metadata_=dependency.metadata,
            )
            .returning(Dependency.id)
        )
        return result.scalar_one_or_none() is not None

    async def delete(self, user_id: UUID, dependency_id: UUID) -> bool:
        result = await self._session.execute(
            delete(Dependency)
            .where(
                Dependency.id == dependency_id,
                self._owned_dependency(user_id),
            )
            .returning(Dependency.id)
        )
        return result.scalar_one_or_none() is not None

    async def _components_are_owned(
        self,
        user_id: UUID,
        source_component_id: UUID,
        target_component_id: UUID,
    ) -> bool:
        return await self._component_is_owned(
            user_id, source_component_id
        ) and await self._component_is_owned(user_id, target_component_id)

    async def _component_is_owned(self, user_id: UUID, component_id: UUID) -> bool:
        source = aliased(CodeComponent)
        repository = aliased(Repository)
        project = aliased(Project)
        result = await self._session.scalar(
            select(
                exists(
                    select(source.id)
                    .select_from(source)
                    .join(repository, repository.id == source.repository_id)
                    .join(project, project.id == repository.project_id)
                    .where(
                        source.id == component_id,
                        repository.deleted_at.is_(None),
                        project.user_id == user_id,
                        project.deleted_at.is_(None),
                    )
                )
            )
        )
        return bool(result)

    @staticmethod
    def _owned_dependency(user_id: UUID) -> Exists:
        source = aliased(CodeComponent)
        target = aliased(CodeComponent)
        source_repository = aliased(Repository)
        target_repository = aliased(Repository)
        source_project = aliased(Project)
        target_project = aliased(Project)
        return exists(
            select(source.id)
            .select_from(source)
            .join(source_repository, source_repository.id == source.repository_id)
            .join(source_project, source_project.id == source_repository.project_id)
            .join(target, target.id == Dependency.target_component_id)
            .join(target_repository, target_repository.id == target.repository_id)
            .join(target_project, target_project.id == target_repository.project_id)
            .where(
                source.id == Dependency.source_component_id,
                source_repository.deleted_at.is_(None),
                source_project.user_id == user_id,
                source_project.deleted_at.is_(None),
                target_repository.deleted_at.is_(None),
                target_project.user_id == user_id,
                target_project.deleted_at.is_(None),
            )
        )

    @staticmethod
    def _to_entity(model: Dependency) -> DependencyEntity:
        return DependencyEntity(
            entity_id=model.id,
            source_component_id=model.source_component_id,
            target_component_id=model.target_component_id,
            dependency_type=model.dependency_type,
            is_directed=model.is_directed,
            source_type=model.source_type,
            confidence=model.confidence,
            analysis_version=model.analysis_version,
            analyzed_at=model.analyzed_at,
            metadata=model.metadata_,
        )

    @staticmethod
    def _to_model(entity: DependencyEntity) -> Dependency:
        return Dependency(
            id=entity.id,
            source_component_id=entity.source_component_id,
            target_component_id=entity.target_component_id,
            dependency_type=entity.dependency_type,
            is_directed=entity.is_directed,
            source_type=entity.source_type,
            confidence=entity.confidence,
            analysis_version=entity.analysis_version,
            analyzed_at=entity.analyzed_at,
            metadata_=entity.metadata,
        )
