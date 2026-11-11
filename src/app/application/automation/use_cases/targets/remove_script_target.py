from typing import Any

from app.application.automation.use_cases.target_operations import TargetOperations


class RemoveScriptTarget(TargetOperations):
    async def remove_script_target(self, *args: Any, **kwargs: Any) -> Any:
        return await super().remove(*args, **kwargs)
