from typing import Any

from app.application.automation.use_cases.script_operations import ScriptOperations


class UpdateScript(ScriptOperations):
    async def update(self, *args: Any, **kwargs: Any) -> Any:
        return await super().update(*args, **kwargs)
