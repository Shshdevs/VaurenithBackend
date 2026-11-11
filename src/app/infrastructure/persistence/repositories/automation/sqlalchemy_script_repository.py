from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update

from app.domain.automation import Script
from app.infrastructure.persistence.models.automation import Script as ScriptModel

from .sqlalchemy_automation_repository_base import (
    SqlAlchemyAutomationRepositoryBase,
)


class SqlAlchemyScriptRepository(SqlAlchemyAutomationRepositoryBase):
    async def get_script(self, user_id: UUID, script_id: UUID) -> Script | None:
        result = await self._session.execute(
            select(ScriptModel).where(
                ScriptModel.id == script_id,
                ScriptModel.deleted_at.is_(None),
                self._owned_script(user_id),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_script(model) if model is not None else None

    async def get_scripts(self, user_id: UUID) -> list[Script]:
        result = await self._session.execute(
            select(ScriptModel)
            .where(ScriptModel.deleted_at.is_(None), self._owned_script(user_id))
            .order_by(ScriptModel.created_at, ScriptModel.id)
        )
        return [self._to_script(row) for row in result.scalars().all()]

    async def create_script(self, user_id: UUID, script: Script) -> None:
        self._session.add(
            ScriptModel(
                id=script.id,
                user_id=user_id,
                project_id=script.project_id,
                name=script.name,
                slug=script.slug,
                description=script.description,
                content=script.content,
                interpreter=script.interpreter,
                execution_type=script.execution_type,
                parameters=script.parameters,
                risk_level=script.risk_level,
                requires_confirmation=script.requires_confirmation,
                version=script.version,
                created_at=script.created_at,
                updated_at=script.updated_at,
            )
        )

    async def update_script(
        self, user_id: UUID, script: Script, expected_version: int
    ) -> bool:
        result = await self._session.execute(
            update(ScriptModel)
            .where(
                ScriptModel.id == script.id,
                ScriptModel.deleted_at.is_(None),
                ScriptModel.version == expected_version,
                self._owned_script(user_id),
            )
            .values(
                project_id=script.project_id,
                name=script.name,
                slug=script.slug,
                description=script.description,
                content=script.content,
                interpreter=script.interpreter,
                execution_type=script.execution_type,
                parameters=script.parameters,
                risk_level=script.risk_level,
                requires_confirmation=script.requires_confirmation,
                version=script.version,
                updated_at=script.updated_at,
            )
            .returning(ScriptModel.id)
        )
        return result.scalar_one_or_none() is not None

    async def delete_script(
        self, user_id: UUID, script_id: UUID, expected_version: int
    ) -> bool:
        now = datetime.now(UTC)
        result = await self._session.execute(
            update(ScriptModel)
            .where(
                ScriptModel.id == script_id,
                ScriptModel.deleted_at.is_(None),
                ScriptModel.version == expected_version,
                self._owned_script(user_id),
            )
            .values(deleted_at=now, updated_at=now, version=expected_version + 1)
            .returning(ScriptModel.id)
        )
        return result.scalar_one_or_none() is not None
