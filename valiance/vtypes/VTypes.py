from abc import ABC
from dataclasses import dataclass
import enum


@dataclass(frozen=True)
class VType(ABC):
    pass


@dataclass(frozen=True)
class NumberType(VType):
    pass


@dataclass(frozen=True)
class StringType(VType):
    pass


@dataclass(frozen=True)
class ListType(VType):
    element_type: VType


@dataclass(frozen=True)
class MinimumRankType(ListType):
    element_type: VType
    min_rank: int


@dataclass(frozen=True)
class ExactRankType(ListType):
    element_type: VType
    rank: int


@dataclass(frozen=True)
class UnionType(VType):
    types: list[VType]


@dataclass(frozen=True)
class IntersectionType(VType):
    types: list[VType]


@dataclass(frozen=True)
class OptionalType(VType):
    base_type: VType


@dataclass(frozen=True)
class TupleType(VType):
    element_types: list[VType]


@dataclass(frozen=True)
class DictionaryType(VType):
    key_type: VType
    value_type: VType


@dataclass(frozen=True)
class FunctionType(VType):
    generics: list[str]
    param_types: list[VType]
    return_type: VType
    where_clauses: list[str]  # Placeholder for where clauses


@dataclass(frozen=True)
class CustomType(VType):
    name: str


class TypeNames(enum.Enum):
    Number = "Number"
    String = "String"
    Dictionary = "Dictionary"
    Function = "Function"
