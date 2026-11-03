from ..common.exceptions import DomainError


class InvalidRepository(DomainError):
    pass


class InvalidBranch(DomainError):
    pass


class InvalidCommit(DomainError):
    pass


class InvalidCommitHash(DomainError):
    pass


class InvalidCodeComponent(DomainError):
    pass


class InvalidDependency(DomainError):
    pass
