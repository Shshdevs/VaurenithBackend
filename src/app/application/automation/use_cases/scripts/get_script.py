from typing import Any

from app.application.automation.use_cases.script_operations import ScriptOperations


class GetScript(ScriptOperations):
    async def get(self, *args: Any, **kwargs: Any) -> Any:
        return await super().get(*args, **kwargs)
