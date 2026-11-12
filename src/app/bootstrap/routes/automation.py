from fastapi import APIRouter

from app.api.routes.v1.automation import build_automation_router
from app.bootstrap.dependencies.automation import (
    add_automation_script_target_dependency,
    create_automation_script_dependency,
    delete_automation_script_dependency,
    get_automation_script_dependency,
    get_automation_script_execution_dependency,
    get_automation_script_executions_dependency,
    get_automation_script_targets_dependency,
    get_pending_automation_script_executions_dependency,
    get_user_automation_scripts_dependency,
    remove_automation_script_target_dependency,
    report_automation_script_execution_result_dependency,
    request_automation_script_execution_dependency,
    start_automation_script_execution_dependency,
    update_automation_script_dependency,
)
from app.bootstrap.dependencies.identity import get_authenticated_identity


def build_automation_api_router() -> APIRouter:
    entity_router = build_automation_router(
        create_automation_script_dependency=create_automation_script_dependency,
        get_automation_script_dependency=get_automation_script_dependency,
        get_user_automation_scripts_dependency=get_user_automation_scripts_dependency,
        update_automation_script_dependency=update_automation_script_dependency,
        delete_automation_script_dependency=delete_automation_script_dependency,
        add_automation_script_target_dependency=add_automation_script_target_dependency,
        get_automation_script_targets_dependency=get_automation_script_targets_dependency,
        remove_automation_script_target_dependency=remove_automation_script_target_dependency,
        request_automation_script_execution_dependency=request_automation_script_execution_dependency,
        get_pending_automation_script_executions_dependency=get_pending_automation_script_executions_dependency,
        get_automation_script_execution_dependency=get_automation_script_execution_dependency,
        get_automation_script_executions_dependency=get_automation_script_executions_dependency,
        start_automation_script_execution_dependency=start_automation_script_execution_dependency,
        report_automation_script_execution_result_dependency=report_automation_script_execution_result_dependency,
        authenticated_identity_dependency=get_authenticated_identity,
    )
    router = APIRouter()
    router.include_router(entity_router)
    return router
