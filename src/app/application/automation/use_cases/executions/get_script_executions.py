from typing import Any

from app.application.automation.use_cases.execution_operations import ExecutionOperations


class GetScriptExecutions(ExecutionOperations):
    async def get_script_executions(self, *args: Any, **kwargs: Any) -> Any:
        return await super().list(*args, **kwargs)
