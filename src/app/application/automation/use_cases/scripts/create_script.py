from typing import Any

from app.application.automation.use_cases.script_operations import ScriptOperations


class CreateScript(ScriptOperations):
    async def create(self, *args: Any, **kwargs: Any) -> Any:
        return await super().create(*args, **kwargs)
