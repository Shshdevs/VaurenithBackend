from typing import Any

from app.application.automation.use_cases.execution_operations import ExecutionOperations


class ReportScriptExecutionResult(ExecutionOperations):
    async def report_script_execution_result(self, *args: Any, **kwargs: Any) -> Any:
        return await super().finish(*args, **kwargs)
