from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.domain.automation import ScriptTarget
from app.infrastructure.persistence.models.automation import Script as ScriptModel
from app.infrastructure.persistence.models.automation import ScriptTarget as TargetModel
from app.infrastructure.persistence.models.infrastructure.device import Device
from app.infrastructure.persistence.models.projects.environment import Environment
from app.infrastructure.persistence.models.projects.project import Project

from .sqlalchemy_automation_repository_base import (
    SqlAlchemyAutomationRepositoryBase,
)


class SqlAlchemyScriptTargetRepository(SqlAlchemyAutomationRepositoryBase):
    async def get_targets(self, user_id: UUID, script_id: UUID) -> list[ScriptTarget]:
        result = await self._session.execute(
            select(TargetModel)
            .join(ScriptModel, ScriptModel.id == TargetModel.script_id)
            .where(TargetModel.script_id == script_id, self._owned_script(user_id))
            .order_by(TargetModel.created_at, TargetModel.id)
        )
        return [self._to_target(row) for row in result.scalars().all()]

    async def create_target(self, user_id: UUID, target: ScriptTarget) -> None:
        script_exists = await self._session.scalar(
            select(ScriptModel.id).where(
                ScriptModel.id == target.script_id,
                ScriptModel.deleted_at.is_(None),
                self._owned_script(user_id),
            )
        )
        if script_exists is None:
            raise ValueError("Script not found")
        device = await self._session.scalar(
            select(Device.id).where(
                Device.id == target.device_id, Device.user_id == user_id
            )
        )
        if device is None:
            raise ValueError("Device not found")
        if target.environment_id is not None:
            environment = await self._session.execute(
                select(Environment.id, Environment.project_id)
                .join(Project, Project.id == Environment.project_id)
                .where(
                    Environment.id == target.environment_id,
                    Project.user_id == user_id,
                    Project.deleted_at.is_(None),
                )
            )
            environment_row = environment.one_or_none()
            if environment_row is None:
                raise ValueError("Environment not found")
            script_project_id = await self._session.scalar(
                select(ScriptModel.project_id).where(ScriptModel.id == target.script_id)
            )
            if (
                script_project_id is not None
                and environment_row.project_id != script_project_id
            ):
                raise ValueError("Environment must belong to the script project")
        duplicate = await self._session.scalar(
            select(TargetModel.id).where(
                TargetModel.script_id == target.script_id,
                TargetModel.device_id == target.device_id,
                TargetModel.environment_id.is_not_distinct_from(target.environment_id),
            )
        )
        if duplicate is not None:
            raise ValueError("Script target already exists")
        self._session.add(
            TargetModel(
                id=target.id,
                script_id=target.script_id,
                device_id=target.device_id,
                environment_id=target.environment_id,
                created_at=target.created_at,
            )
        )
        try:
            await self._session.flush()
        except IntegrityError as error:
            raise ValueError("Script target already exists") from error

    async def delete_target(self, user_id: UUID, script_id: UUID, target_id: UUID) -> bool:
        target = await self._session.scalar(
            select(TargetModel)
            .join(ScriptModel, ScriptModel.id == TargetModel.script_id)
            .where(
                TargetModel.id == target_id,
                TargetModel.script_id == script_id,
                self._owned_script(user_id),
            )
        )
        if target is None:
            return False
        await self._session.delete(target)
        return True
