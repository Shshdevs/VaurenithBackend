from typing import Any

from app.application.automation.use_cases.execution_operations import ExecutionOperations


class RequestScriptExecution(ExecutionOperations):
    async def request_script_execution(self, *args: Any, **kwargs: Any) -> Any:
        return await super().request(*args, **kwargs)
