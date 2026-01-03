from abc import ABC
from dataclasses import dataclass, field
import enum
from typing import Tuple

from valiance.compiler_common.Identifier import Identifier


@dataclass
class DataTag(ABC):
    name: Identifier
    depth: int


@dataclass
class ElementTag(ABC):
    name: Identifier


@dataclass
class NegateElementTag(ElementTag):
    pass


@dataclass(frozen=True, kw_only=True)
class VType(ABC):
    data_tags: tuple[DataTag, ...] = field(default_factory=tuple)
    element_tags: tuple[ElementTag, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class NumberType(VType):
    pass


@dataclass(frozen=True)
class StringType(VType):
    pass


@dataclass(frozen=True)
class ListType(VType):
    element_type: VType
    rank: (
        int | str
    )  # int if rank is expressed as numbers, str if it's depedent on where


@dataclass(frozen=True)
class MinimumRankType(ListType):
    element_type: VType


@dataclass(frozen=True)
class ExactRankType(ListType):
    element_type: VType


@dataclass(frozen=True)
class UnionType(VType):
    left: VType
    right: VType


@dataclass(frozen=True)
class IntersectionType(VType):
    left: VType
    right: VType


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
    fully_typed: bool
    generics: list[str]
    param_types: list[VType]
    return_types: list[VType]
    where_clauses: list[str]  # Placeholder for where clauses


@dataclass(frozen=True)
class CustomType(VType):
    name: Identifier
    left_types: list[VType]
    right_types: list[VType]


@dataclass(frozen=True)
class AnonymousGeneric(VType):
    identifier: int


@dataclass(frozen=True)
class ErrorType(VType):
    pass


class TypeNames(enum.Enum):
    Number = "Number"
    String = "String"
    Dictionary = "Dictionary"
    Function = "Function"


def type_name_to_vtype(
    _type_name: Identifier,
    generics: Tuple[list[VType], list[VType]],
    data_tags: list[DataTag],
    element_tags: list[ElementTag],
) -> VType:
    type_name = _type_name.name
    if type_name == TypeNames.Number.value:
        if generics[0] or generics[1]:
            raise ValueError("Number type does not accept generics")
        return NumberType(data_tags=tuple(data_tags), element_tags=tuple(element_tags))
    elif type_name == TypeNames.String.value:
        if generics[0] or generics[1]:
            raise ValueError("String type does not accept generics")
        return StringType(data_tags=tuple(data_tags), element_tags=tuple(element_tags))
    elif type_name == TypeNames.Dictionary.value:
        if len(generics[0]) > 1:
            raise ValueError("Dictionary type given more than 1 key type")
        if len(generics[1]) > 1:
            raise ValueError("Dictionary type given more than 1 value type")
        return DictionaryType(
            generics[0][0],
            generics[1][0],
            data_tags=tuple(data_tags),
            element_tags=tuple(element_tags),
        )
    elif type_name == TypeNames.Function.value:
        return FunctionType(
            True,
            [],
            generics[0],
            generics[1],
            [],
            data_tags=tuple(data_tags),
            element_tags=tuple(element_tags),
        )
    else:
        return CustomType(
            name=_type_name,
            left_types=generics[0],
            right_types=generics[1],
            data_tags=tuple(data_tags),
            element_tags=tuple(element_tags),
        )
