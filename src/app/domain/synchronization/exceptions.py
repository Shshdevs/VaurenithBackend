from ..common.exceptions import DomainError


class InvalidChangeLog(DomainError):
    pass


class InvalidSyncState(DomainError):
    pass
