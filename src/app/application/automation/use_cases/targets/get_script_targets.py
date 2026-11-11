from typing import Any

from app.application.automation.use_cases.target_operations import TargetOperations


class GetScriptTargets(TargetOperations):
    async def get_script_targets(self, *args: Any, **kwargs: Any) -> Any:
        return await super().list(*args, **kwargs)
