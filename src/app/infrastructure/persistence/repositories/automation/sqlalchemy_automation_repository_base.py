from uuid import UUID

from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.automation import Script, ScriptExecution, ScriptTarget
from app.infrastructure.persistence.models.automation import Script as ScriptModel
from app.infrastructure.persistence.models.automation import (
    ScriptExecution as ExecutionModel,
)
from app.infrastructure.persistence.models.automation import ScriptTarget as TargetModel
from app.infrastructure.persistence.models.projects.project import Project


class SqlAlchemyAutomationRepositoryBase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _owned_script(self, user_id: UUID):
        return or_(
            ScriptModel.user_id == user_id,
            exists(
                select(Project.id).where(
                    Project.id == ScriptModel.project_id,
                    Project.user_id == user_id,
                    Project.deleted_at.is_(None),
                )
            ),
        )

    @staticmethod
    def _to_script(model: ScriptModel) -> Script:
        return Script(
            entity_id=model.id,
            project_id=model.project_id,
            name=model.name,
            description=model.description,
            content=model.content,
            interpreter=model.interpreter,
            execution_type=model.execution_type,
            parameters=model.parameters,
            risk_level=model.risk_level,
            requires_confirmation=model.requires_confirmation,
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _to_target(model: TargetModel) -> ScriptTarget:
        return ScriptTarget(
            entity_id=model.id,
            script_id=model.script_id,
            device_id=model.device_id,
            environment_id=model.environment_id,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_execution(model: ExecutionModel) -> ScriptExecution:
        return ScriptExecution(
            entity_id=model.id,
            script_id=model.script_id,
            device_id=model.device_id,
            client_device_id=model.client_device_id,
            parameters=model.parameters,
            status=model.status,
            exit_code=model.exit_code,
            started_at=model.started_at,
            finished_at=model.finished_at,
            error_message=model.error_message,
            sanitized_output_summary=model.sanitized_output_summary,
            idempotency_key=model.idempotency_key,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_execution_model(entity: ScriptExecution) -> ExecutionModel:
        return ExecutionModel(
            id=entity.id,
            script_id=entity.script_id,
            device_id=entity.device_id,
            client_device_id=entity.client_device_id,
            parameters=entity.parameters,
            status=entity.status,
            exit_code=entity.exit_code,
            started_at=entity.started_at,
            finished_at=entity.finished_at,
            error_message=entity.error_message,
            sanitized_output_summary=entity.sanitized_output_summary,
            idempotency_key=entity.idempotency_key,
            created_at=entity.created_at,
        )
