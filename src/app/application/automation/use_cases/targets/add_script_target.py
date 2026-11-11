from typing import Any

from app.application.automation.use_cases.target_operations import TargetOperations


class AddScriptTarget(TargetOperations):
    async def add_script_target(self, *args: Any, **kwargs: Any) -> Any:
        return await super().add(*args, **kwargs)
