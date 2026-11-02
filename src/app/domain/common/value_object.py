from abc import ABC, abstractmethod
from collections.abc import Hashable


class ValueObject(ABC):
    @abstractmethod
    def equality_components(self) -> tuple[Hashable, ...]:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        return (
            type(self) is type(other)
            and isinstance(other, ValueObject)
            and self.equality_components() == other.equality_components()
        )

    def __hash__(self) -> int:
        return hash((type(self), self.equality_components()))
