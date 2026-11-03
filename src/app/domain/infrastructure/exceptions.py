from ..common.exceptions import DomainError


class InvalidDevice(DomainError):
    pass


class InvalidConnection(DomainError):
    pass


class InvalidService(DomainError):
    pass


class InvalidContainer(DomainError):
    pass


class InvalidDatabase(DomainError):
    pass
