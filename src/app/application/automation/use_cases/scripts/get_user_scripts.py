from typing import Any

from app.application.automation.use_cases.script_operations import ScriptOperations


class GetUserScripts(ScriptOperations):
    async def get_user_scripts(self, *args: Any, **kwargs: Any) -> Any:
        return await super().list(*args, **kwargs)
