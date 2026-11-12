from uuid import UUID

from sqlalchemy import delete, exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Exists

from app.application.development.interfaces import BranchRepository
from app.domain.development.entities.branch import Branch as BranchEntity
from app.infrastructure.persistence.models.development.branch import Branch
from app.infrastructure.persistence.models.development.repository import Repository
from app.infrastructure.persistence.models.projects.project import Project


class SqlAlchemyBranchRepository(BranchRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID, branch_id: UUID) -> BranchEntity | None:
        result = await self._session.execute(
            select(Branch)
            .join(Repository, Repository.id == Branch.repository_id)
            .where(
                Branch.id == branch_id,
                self._owned_repository(user_id, Branch.repository_id),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def get_by_repository(
        self, user_id: UUID, repository_id: UUID
    ) -> list[BranchEntity]:
        result = await self._session.execute(
            select(Branch)
            .join(Repository, Repository.id == Branch.repository_id)
            .where(
                Branch.repository_id == repository_id,
                self._owned_repository(user_id, Branch.repository_id),
            )
            .order_by(Branch.is_remote, Branch.name, Branch.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_name(
        self, user_id: UUID, repository_id: UUID, name: str, is_remote: bool
    ) -> BranchEntity | None:
        result = await self._session.execute(
            select(Branch)
            .join(Repository, Repository.id == Branch.repository_id)
            .where(
                Branch.repository_id == repository_id,
                Branch.name == name,
                Branch.is_remote == is_remote,
                self._owned_repository(user_id, Branch.repository_id),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def create(self, user_id: UUID, branch: BranchEntity) -> None:
        if not await self._repository_is_owned(user_id, branch.repository_id):
            raise ValueError("Repository not found")
        if branch.is_current:
            if not await self._lock_repository(user_id, branch.repository_id):
                raise ValueError("Repository not found")
            await self._clear_current_branches(user_id, branch.repository_id)
        self._session.add(self._to_model(branch))

    async def update(self, user_id: UUID, branch: BranchEntity) -> bool:
        existing = await self._session.scalar(
            select(Branch.id)
            .join(Repository, Repository.id == Branch.repository_id)
            .where(
                Branch.id == branch.id,
                self._owned_repository(user_id, Branch.repository_id),
            )
        )
        if existing is None:
            return False
        if branch.is_current:
            if not await self._lock_repository(user_id, branch.repository_id):
                return False
            await self._clear_current_branches(user_id, branch.repository_id, branch.id)
        result = await self._session.execute(
            update(Branch)
            .where(
                Branch.id == branch.id,
                Branch.repository_id == branch.repository_id,
                self._owned_repository(user_id, Branch.repository_id),
            )
            .values(
                name=branch.name,
                commit_hash=branch.commit_hash,
                is_remote=branch.is_remote,
                is_current=branch.is_current,
                last_updated_at=branch.last_updated_at,
                last_synced_at=branch.last_synced_at,
            )
            .returning(Branch.id)
        )
        return result.scalar_one_or_none() is not None

    async def delete(self, user_id: UUID, branch_id: UUID) -> bool:
        result = await self._session.execute(
            delete(Branch)
            .where(
                Branch.id == branch_id,
                self._owned_repository(user_id, Branch.repository_id),
            )
            .returning(Branch.id)
        )
        return result.scalar_one_or_none() is not None

    async def _clear_current_branches(
        self,
        user_id: UUID,
        repository_id: UUID,
        excluded_branch_id: UUID | None = None,
    ) -> None:
        statement = update(Branch).where(
            Branch.repository_id == repository_id,
            Branch.is_current.is_(True),
            self._owned_repository(user_id, Branch.repository_id),
        )
        if excluded_branch_id is not None:
            statement = statement.where(Branch.id != excluded_branch_id)
        await self._session.execute(statement.values(is_current=False))

    async def _repository_is_owned(self, user_id: UUID, repository_id: UUID) -> bool:
        return bool(
            await self._session.scalar(
                select(self._owned_repository(user_id, repository_id))
            )
        )

    async def _lock_repository(self, user_id: UUID, repository_id: UUID) -> bool:
        result = await self._session.scalar(
            select(Repository.id)
            .join(Project, Project.id == Repository.project_id)
            .where(
                Repository.id == repository_id,
                Repository.deleted_at.is_(None),
                Project.user_id == user_id,
                Project.deleted_at.is_(None),
            )
            .with_for_update(of=Repository)
        )
        return result is not None

    @staticmethod
    def _owned_repository(user_id: UUID, repository_id) -> Exists:
        return exists(
            select(Repository.id)
            .join(Project, Project.id == Repository.project_id)
            .where(
                Repository.id == repository_id,
                Project.user_id == user_id,
                Project.deleted_at.is_(None),
                Repository.deleted_at.is_(None),
            )
            .correlate_except(Repository)
        )

    @staticmethod
    def _to_entity(model: Branch) -> BranchEntity:
        return BranchEntity(
            entity_id=model.id,
            repository_id=model.repository_id,
            name=model.name,
            commit_hash=model.commit_hash,
            is_remote=model.is_remote,
            is_current=model.is_current,
            last_updated_at=model.last_updated_at,
            last_synced_at=model.last_synced_at,
        )

    @staticmethod
    def _to_model(entity: BranchEntity) -> Branch:
        return Branch(
            id=entity.id,
            repository_id=entity.repository_id,
            name=entity.name,
            commit_hash=entity.commit_hash,
            is_remote=entity.is_remote,
            is_current=entity.is_current,
            last_updated_at=entity.last_updated_at,
            last_synced_at=entity.last_synced_at,
        )
