from ..common.exceptions import DomainError


class InvalidScript(DomainError):
    pass


class InvalidScriptExecution(DomainError):
    pass


class InvalidScriptTarget(DomainError):
    pass
