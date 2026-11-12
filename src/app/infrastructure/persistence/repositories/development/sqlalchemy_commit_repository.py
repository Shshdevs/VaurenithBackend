from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Exists

from app.application.development.interfaces import CommitRepository
from app.domain.development.entities.commit import Commit as CommitEntity
from app.infrastructure.persistence.models.development.commit import Commit
from app.infrastructure.persistence.models.development.repository import Repository
from app.infrastructure.persistence.models.projects.project import Project


class SqlAlchemyCommitRepository(CommitRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID, commit_id: UUID) -> CommitEntity | None:
        result = await self._session.execute(
            select(Commit)
            .join(Repository, Repository.id == Commit.repository_id)
            .where(Commit.id == commit_id, self._owned_repository(user_id))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def get_by_repository(
        self, user_id: UUID, repository_id: UUID
    ) -> list[CommitEntity]:
        result = await self._session.execute(
            select(Commit)
            .join(Repository, Repository.id == Commit.repository_id)
            .where(
                Commit.repository_id == repository_id,
                self._owned_repository(user_id),
            )
            .order_by(Commit.committed_at.desc().nullslast(), Commit.hash, Commit.id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_hash(
        self, user_id: UUID, repository_id: UUID, commit_hash: str
    ) -> CommitEntity | None:
        result = await self._session.execute(
            select(Commit)
            .join(Repository, Repository.id == Commit.repository_id)
            .where(
                Commit.repository_id == repository_id,
                Commit.hash == commit_hash,
                self._owned_repository(user_id),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def create(self, user_id: UUID, commit: CommitEntity) -> None:
        if not await self._repository_is_owned(user_id, commit.repository_id):
            raise ValueError("Repository not found")
        self._session.add(self._to_model(commit))

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
    def _to_entity(model: Commit) -> CommitEntity:
        return CommitEntity(
            entity_id=model.id,
            repository_id=model.repository_id,
            hash=model.hash,
            author_name=model.author_name,
            author_email=model.author_email,
            message=model.message,
            committed_at=model.committed_at,
            changed_files=model.changed_files,
            cached_at=model.cached_at,
        )

    @staticmethod
    def _to_model(entity: CommitEntity) -> Commit:
        return Commit(
            id=entity.id,
            repository_id=entity.repository_id,
            hash=entity.hash,
            author_name=entity.author_name,
            author_email=entity.author_email,
            message=entity.message,
            committed_at=entity.committed_at,
            changed_files=entity.changed_files,
            cached_at=entity.cached_at,
        )
