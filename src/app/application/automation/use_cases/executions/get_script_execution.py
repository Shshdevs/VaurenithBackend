from typing import Any

from app.application.automation.use_cases.execution_operations import ExecutionOperations


class GetScriptExecution(ExecutionOperations):
    async def get_script_execution(self, *args: Any, **kwargs: Any) -> Any:
        return await super().get(*args, **kwargs)
