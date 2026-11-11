from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.automation import (
    GetPendingScriptExecutions,
    GetScriptExecution,
    GetScriptExecutions,
    ReportScriptExecutionResult,
    RequestScriptExecution,
    StartScriptExecution,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.automation import (
    provide_get_pending_script_executions,
    provide_get_script_execution,
    provide_get_script_executions,
    provide_report_script_execution_result,
    provide_request_script_execution,
    provide_start_script_execution,
)


def request_automation_script_execution_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> RequestScriptExecution:
    return provide_request_script_execution(session)


def get_pending_automation_script_executions_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetPendingScriptExecutions:
    return provide_get_pending_script_executions(session)


def start_automation_script_execution_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> StartScriptExecution:
    return provide_start_script_execution(session)


def report_automation_script_execution_result_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> ReportScriptExecutionResult:
    return provide_report_script_execution_result(session)


def get_automation_script_execution_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetScriptExecution:
    return provide_get_script_execution(session)


def get_automation_script_executions_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetScriptExecutions:
    return provide_get_script_executions(session)
