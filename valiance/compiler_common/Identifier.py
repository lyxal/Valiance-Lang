from abc import ABC
from dataclasses import dataclass
from typing import Generic, TypeVar


class Identifier:
    def __init__(
        self,
        name: str = "",
        property: Identifier | None = None,
        is_error: bool = False,
        index: StaticIndex | None = None,
    ):
        self.name: str = name
        self.property: Identifier | None = property
        self.error: bool = is_error
        self.index: StaticIndex | None = index

    def __repr__(self):
        # Construct the full identifier representation based on properties and indexing
        repr_str = self.name
        if self.index is not None:
            repr_str += f"[{self.index}]"
        if self.property is not None:
            repr_str += f".{self.property}"
        return repr_str

    def __str__(self):
        return self.__repr__()


X = TypeVar("X", bound="ScalarIndex | MDIndex | ScalarVariableIndex | ErrorIndex")


@dataclass(frozen=True)
class StaticIndex(ABC):
    pass


@dataclass(frozen=True)
class ScalarIndex(StaticIndex):
    index: int

    def __repr__(self):
        return f"{self.index}"


@dataclass(frozen=True)
class ScalarVariableIndex(StaticIndex):
    name: Identifier

    def __repr__(self):
        return f"${self.name}"


@dataclass(frozen=True)
class SliceIndex(StaticIndex, Generic[X]):
    start: X | None
    stop: X | None
    step: X | None

    def __repr__(self):
        start_str = str(self.start) if self.start is not None else ""
        stop_str = str(self.stop) if self.stop is not None else ""
        step_str = str(self.step) if self.step is not None else ""
        if self.step is not None:
            return f"{start_str}:{stop_str}:{step_str}"
        else:
            return f"{start_str}:{stop_str}"


@dataclass(frozen=True)
class MDIndex(StaticIndex):
    indices: list[ScalarIndex | ScalarVariableIndex]

    def __repr__(self):
        return ",".join(str(i) for i in self.indices)


@dataclass(frozen=True)
class ErrorIndex(StaticIndex):
    pass

    def __repr__(self):
        return "ErrorIndex"
