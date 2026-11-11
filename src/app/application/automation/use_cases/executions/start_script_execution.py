from typing import Any

from app.application.automation.use_cases.execution_operations import ExecutionOperations


class StartScriptExecution(ExecutionOperations):
    async def start_script_execution(self, *args: Any, **kwargs: Any) -> Any:
        return await super().start(*args, **kwargs)
