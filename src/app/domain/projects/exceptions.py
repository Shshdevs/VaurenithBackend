from ..common.exceptions import DomainError


class InvalidEnvironment(DomainError):
    pass


class InvalidProject(DomainError):
    pass


class InvalidProjectDeviceRelation(DomainError):
    pass
