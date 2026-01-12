from abc import abstractmethod
from dataclasses import dataclass
import typing

KEY_TYPE = typing.TypeVar("KEY_TYPE")
VALUE_TYPE = typing.TypeVar("VALUE_TYPE")


@dataclass(frozen=True)
class AbstractQueryKey:
    @abstractmethod
    def __hash__(self) -> int:
        pass


class AbstractQueryEngine(typing.Generic[KEY_TYPE, VALUE_TYPE]):
    def __init__(self):
        self._cache: dict[KEY_TYPE, VALUE_TYPE] = {}

    def query(self, key: KEY_TYPE) -> VALUE_TYPE | None:
        return self._cache.get(key, None)

    def store(self, key: KEY_TYPE, value: VALUE_TYPE) -> None:
        self._cache[key] = value
