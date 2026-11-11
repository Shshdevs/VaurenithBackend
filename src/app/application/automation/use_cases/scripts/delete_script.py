from typing import Any

from app.application.automation.use_cases.script_operations import ScriptOperations


class DeleteScript(ScriptOperations):
    async def delete(self, *args: Any, **kwargs: Any) -> Any:
        return await super().delete(*args, **kwargs)
