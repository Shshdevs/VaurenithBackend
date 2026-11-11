from typing import Any

from app.application.automation.use_cases.execution_operations import ExecutionOperations


class GetPendingScriptExecutions(ExecutionOperations):
    async def get_pending_script_executions(self, *args: Any, **kwargs: Any) -> Any:
        return await super().pending(*args, **kwargs)
