from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.schemas.response import ApiResponse, format_http_status
from app.api.schemas.v1.automation import (
    ScriptCreateRequest,
    ScriptData,
    ScriptExecutionData,
    ScriptExecutionQueueItem,
    ScriptExecutionRequest,
    ScriptExecutionResultRequest,
    ScriptExecutionStartRequest,
    ScriptTargetCreateRequest,
    ScriptTargetData,
    ScriptUpdateRequest,
)
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
from app.application.identity import VerifiedIdentity


def build_automation_router(
    create_automation_script_dependency: Callable[..., CreateScript],
    get_automation_script_dependency: Callable[..., GetScript],
    get_user_automation_scripts_dependency: Callable[..., GetUserScripts],
    update_automation_script_dependency: Callable[..., UpdateScript],
    delete_automation_script_dependency: Callable[..., DeleteScript],
    add_automation_script_target_dependency: Callable[..., AddScriptTarget],
    get_automation_script_targets_dependency: Callable[..., GetScriptTargets],
    remove_automation_script_target_dependency: Callable[..., RemoveScriptTarget],
    request_automation_script_execution_dependency: Callable[..., RequestScriptExecution],
    get_pending_automation_script_executions_dependency: Callable[
        ..., GetPendingScriptExecutions
    ],
    get_automation_script_execution_dependency: Callable[..., GetScriptExecution],
    get_automation_script_executions_dependency: Callable[..., GetScriptExecutions],
    start_automation_script_execution_dependency: Callable[..., StartScriptExecution],
    report_automation_script_execution_result_dependency: Callable[
        ..., ReportScriptExecutionResult
    ],
    authenticated_identity_dependency: Callable[
        ..., VerifiedIdentity | Awaitable[VerifiedIdentity]
    ],
) -> APIRouter:
    router = APIRouter(tags=["automation"])

    @router.post(
        "/scripts",
        response_model=ApiResponse[ScriptData],
        status_code=status.HTTP_201_CREATED,
    )
    async def create_script(
        request: ScriptCreateRequest,
        use_case: CreateScript = Depends(create_automation_script_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ScriptData]:
        script = await use_case.create(identity, **request.model_dump())
        return ApiResponse(
            status=format_http_status(status.HTTP_201_CREATED),
            message="Script created successfully",
            data=ScriptData.model_validate(script),
        )

    @router.get("/scripts", response_model=ApiResponse[list[ScriptData]])
    async def list_scripts(
        use_case: GetUserScripts = Depends(get_user_automation_scripts_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ScriptData]]:
        scripts = await use_case.get_user_scripts(identity)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=[ScriptData.model_validate(script) for script in scripts],
        )

    @router.get("/scripts/{script_id}", response_model=ApiResponse[ScriptData])
    async def get_script(
        script_id: UUID,
        use_case: GetScript = Depends(get_automation_script_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ScriptData]:
        script = await use_case.get(identity, script_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=ScriptData.model_validate(script),
        )

    @router.put("/scripts/{script_id}", response_model=ApiResponse[ScriptData])
    async def update_script(
        script_id: UUID,
        request: ScriptUpdateRequest,
        use_case: UpdateScript = Depends(update_automation_script_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ScriptData]:
        values = request.model_dump()
        version = values.pop("version")
        script = await use_case.update(identity, script_id, version, **values)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=ScriptData.model_validate(script),
        )

    @router.delete("/scripts/{script_id}", response_model=ApiResponse[None])
    async def delete_script(
        script_id: UUID,
        expected_version: int = Query(ge=1, le=2**63 - 2),
        use_case: DeleteScript = Depends(delete_automation_script_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await use_case.delete(identity, script_id, expected_version)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            message="Script deleted successfully",
        )

    @router.get(
        "/scripts/{script_id}/targets",
        response_model=ApiResponse[list[ScriptTargetData]],
    )
    async def list_targets(
        script_id: UUID,
        use_case: GetScriptTargets = Depends(get_automation_script_targets_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ScriptTargetData]]:
        targets = await use_case.get_script_targets(identity, script_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=[ScriptTargetData.model_validate(target) for target in targets],
        )

    @router.post(
        "/scripts/{script_id}/targets",
        response_model=ApiResponse[ScriptTargetData],
        status_code=status.HTTP_201_CREATED,
    )
    async def add_target(
        script_id: UUID,
        request: ScriptTargetCreateRequest,
        use_case: AddScriptTarget = Depends(add_automation_script_target_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ScriptTargetData]:
        target = await use_case.add_script_target(
            identity, script_id, **request.model_dump()
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_201_CREATED),
            data=ScriptTargetData.model_validate(target),
        )

    @router.delete(
        "/scripts/{script_id}/targets/{target_id}",
        response_model=ApiResponse[None],
    )
    async def remove_target(
        script_id: UUID,
        target_id: UUID,
        use_case: RemoveScriptTarget = Depends(remove_automation_script_target_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[None]:
        await use_case.remove_script_target(identity, script_id, target_id)
        return ApiResponse(status=format_http_status(status.HTTP_200_OK))

    @router.post(
        "/scripts/{script_id}/executions",
        response_model=ApiResponse[ScriptExecutionData],
        status_code=status.HTTP_201_CREATED,
    )
    async def request_execution(
        script_id: UUID,
        request: ScriptExecutionRequest,
        use_case: RequestScriptExecution = Depends(
            request_automation_script_execution_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ScriptExecutionData]:
        execution = await use_case.request_script_execution(
            identity, script_id, **request.model_dump()
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_201_CREATED),
            data=ScriptExecutionData.model_validate(execution),
        )

    @router.get(
        "/script-executions/pending",
        response_model=ApiResponse[list[ScriptExecutionQueueItem]],
    )
    async def get_pending_executions(
        client_device_id: UUID,
        executions_use_case: GetPendingScriptExecutions = Depends(
            get_pending_automation_script_executions_dependency
        ),
        scripts_use_case: GetScript = Depends(get_automation_script_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ScriptExecutionQueueItem]]:
        executions = await executions_use_case.get_pending_script_executions(
            identity, client_device_id
        )
        queue = [
            ScriptExecutionQueueItem(
                execution=ScriptExecutionData.model_validate(execution),
                script=ScriptData.model_validate(
                    await scripts_use_case.get(identity, execution.script_id)
                ),
            )
            for execution in executions
        ]
        return ApiResponse(status=format_http_status(status.HTTP_200_OK), data=queue)

    @router.get(
        "/script-executions",
        response_model=ApiResponse[list[ScriptExecutionData]],
    )
    async def list_executions(
        script_id: UUID | None = None,
        use_case: GetScriptExecutions = Depends(
            get_automation_script_executions_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[list[ScriptExecutionData]]:
        executions = await use_case.get_script_executions(identity, script_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=[ScriptExecutionData.model_validate(item) for item in executions],
        )

    @router.get(
        "/script-executions/{execution_id}",
        response_model=ApiResponse[ScriptExecutionData],
    )
    async def get_execution(
        execution_id: UUID,
        use_case: GetScriptExecution = Depends(get_automation_script_execution_dependency),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ScriptExecutionData]:
        execution = await use_case.get_script_execution(identity, execution_id)
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=ScriptExecutionData.model_validate(execution),
        )

    @router.post(
        "/script-executions/{execution_id}/start",
        response_model=ApiResponse[ScriptExecutionData],
    )
    async def start_execution(
        execution_id: UUID,
        request: ScriptExecutionStartRequest,
        use_case: StartScriptExecution = Depends(
            start_automation_script_execution_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ScriptExecutionData]:
        execution = await use_case.start_script_execution(
            identity, execution_id, request.client_device_id
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=ScriptExecutionData.model_validate(execution),
        )

    @router.put(
        "/script-executions/{execution_id}/result",
        response_model=ApiResponse[ScriptExecutionData],
    )
    async def finish_execution(
        execution_id: UUID,
        request: ScriptExecutionResultRequest,
        use_case: ReportScriptExecutionResult = Depends(
            report_automation_script_execution_result_dependency
        ),
        identity: VerifiedIdentity = Depends(authenticated_identity_dependency),
    ) -> ApiResponse[ScriptExecutionData]:
        execution = await use_case.report_script_execution_result(
            identity,
            execution_id,
            request.client_device_id,
            request.status.value,
            request.exit_code,
            request.error_message,
            request.sanitized_output_summary,
        )
        return ApiResponse(
            status=format_http_status(status.HTTP_200_OK),
            data=ScriptExecutionData.model_validate(execution),
        )

    return router
