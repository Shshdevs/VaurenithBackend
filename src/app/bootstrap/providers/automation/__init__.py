from sqlalchemy.ext.asyncio import AsyncSession

from app.application.automation import (
    AddScriptTarget,
    CreateScript,
    DeleteScript,
    GetPendingScriptExecutions,
    GetScript,
    GetScriptExecution,
    GetScriptExecutions,
    GetScriptTargets,
    GetUserScripts,
    RemoveScriptTarget,
    ReportScriptExecutionResult,
    RequestScriptExecution,
    StartScriptExecution,
    UpdateScript,
)
from app.application.synchronization.use_cases.change_log import RecordChange
from app.infrastructure.persistence.repositories.automation import (
    SqlAlchemyScriptExecutionRepository,
    SqlAlchemyScriptRepository,
    SqlAlchemyScriptTargetRepository,
)
from app.infrastructure.persistence.repositories.projects import SqlAlchemyProjectRepository
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def _script_dependencies(session: AsyncSession):
    return (
        SqlAlchemyScriptRepository(session),
        SqlAlchemyProjectRepository(session),
        RecordChange(SqlAlchemyChangeLogRepository(session)),
        SqlAlchemyUnitOfWork(session),
        SqlAlchemyScriptExecutionRepository(session),
    )


def _target_dependencies(session: AsyncSession):
    return (
        SqlAlchemyScriptRepository(session),
        SqlAlchemyScriptTargetRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def _execution_dependencies(session: AsyncSession):
    return (
        SqlAlchemyScriptRepository(session),
        SqlAlchemyScriptExecutionRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_create_script(session: AsyncSession) -> CreateScript:
    return CreateScript(*_script_dependencies(session))


def provide_get_script(session: AsyncSession) -> GetScript:
    return GetScript(*_script_dependencies(session))


def provide_get_user_scripts(session: AsyncSession) -> GetUserScripts:
    return GetUserScripts(*_script_dependencies(session))


def provide_update_script(session: AsyncSession) -> UpdateScript:
    return UpdateScript(*_script_dependencies(session))


def provide_delete_script(session: AsyncSession) -> DeleteScript:
    return DeleteScript(*_script_dependencies(session))


def provide_add_script_target(session: AsyncSession) -> AddScriptTarget:
    return AddScriptTarget(*_target_dependencies(session))


def provide_get_script_targets(session: AsyncSession) -> GetScriptTargets:
    return GetScriptTargets(*_target_dependencies(session))


def provide_remove_script_target(session: AsyncSession) -> RemoveScriptTarget:
    return RemoveScriptTarget(*_target_dependencies(session))


def provide_request_script_execution(session: AsyncSession) -> RequestScriptExecution:
    return RequestScriptExecution(*_execution_dependencies(session))


def provide_get_pending_script_executions(
    session: AsyncSession,
) -> GetPendingScriptExecutions:
    return GetPendingScriptExecutions(*_execution_dependencies(session))


def provide_start_script_execution(session: AsyncSession) -> StartScriptExecution:
    return StartScriptExecution(*_execution_dependencies(session))


def provide_report_script_execution_result(
    session: AsyncSession,
) -> ReportScriptExecutionResult:
    return ReportScriptExecutionResult(*_execution_dependencies(session))


def provide_get_script_execution(session: AsyncSession) -> GetScriptExecution:
    return GetScriptExecution(*_execution_dependencies(session))


def provide_get_script_executions(session: AsyncSession) -> GetScriptExecutions:
    return GetScriptExecutions(*_execution_dependencies(session))
