from abc import ABC, abstractmethod
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

    @abstractmethod
    def toString(self) -> str:
        pass

    def formatthis(self):
        # Data tags is a space separated list of tag names
        data_tags_str = " ".join("#" + tag.name.name for tag in self.data_tags)
        # Element tags is a space separated list of tag names, with negation if applicable
        element_tags_str = " ".join(
            ("- " if isinstance(tag, NegateElementTag) else "+ ") + tag.name.name
            for tag in self.element_tags
        )

        return f"{data_tags_str} {self.toString()} {element_tags_str}".strip()


@dataclass(frozen=True)
class NumberType(VType):
    pass

    def toString(self) -> str:
        return "Number"


@dataclass(frozen=True)
class StringType(VType):
    pass

    def toString(self) -> str:
        return "String"


@dataclass(frozen=True)
class ListType(VType):
    element_type: VType
    rank: (
        int | str
    )  # int if rank is expressed as numbers, str if it's depedent on where

    def toString(self) -> str:
        rank_str = str("~" * self.rank) if isinstance(self.rank, int) else self.rank
        return f"{self.element_type.formatthis()}{rank_str}"


@dataclass(frozen=True)
class MinimumRankType(ListType):
    element_type: VType

    def toString(self) -> str:
        rank_str = str("*" * self.rank) if isinstance(self.rank, int) else self.rank
        return f"{self.element_type.formatthis()}{rank_str}+"


@dataclass(frozen=True)
class ExactRankType(ListType):
    element_type: VType

    def toString(self) -> str:
        rank_str = str("+" * self.rank) if isinstance(self.rank, int) else self.rank
        return f"{self.element_type.formatthis()}{rank_str}"


@dataclass(frozen=True)
class UnionType(VType):
    left: VType
    right: VType

    def toString(self) -> str:
        return f"({self.left.formatthis()} | {self.right.formatthis()})"


@dataclass(frozen=True)
class IntersectionType(VType):
    left: VType
    right: VType

    def toString(self) -> str:
        return f"({self.left.formatthis()} & {self.right.formatthis()})"


@dataclass(frozen=True)
class OptionalType(VType):
    base_type: VType

    def toString(self) -> str:
        return f"{self.base_type.formatthis()}?"


@dataclass(frozen=True)
class TupleType(VType):
    element_types: list[VType]

    def toString(self) -> str:
        element_types_str = ", ".join(t.formatthis() for t in self.element_types)
        return f"({element_types_str})"


@dataclass(frozen=True)
class DictionaryType(VType):
    key_type: VType
    value_type: VType

    def toString(self) -> str:
        return f"Dictionary[{self.key_type.formatthis()} -> {self.value_type.formatthis()}]"


@dataclass(frozen=True)
class FunctionType(VType):
    fully_typed: bool
    generics: list[str]
    param_types: list[VType]
    return_types: list[VType]
    where_clauses: list[str]  # Placeholder for where clauses

    def toString(self) -> str:
        param_types_str = ", ".join(t.formatthis() for t in self.param_types)
        return_types_str = ", ".join(t.formatthis() for t in self.return_types)
        return f"Function[{param_types_str} -> {return_types_str}]"


@dataclass(frozen=True)
class CustomType(VType):
    name: Identifier
    left_types: list[VType]
    right_types: list[VType]

    def toString(self) -> str:
        if self.left_types and self.right_types:
            left_str = ", ".join(t.formatthis() for t in self.left_types)
            right_str = ", ".join(t.formatthis() for t in self.right_types)
            return f"{self.name}[{left_str} -> {right_str}]"
        elif self.left_types:
            left_str = ", ".join(t.formatthis() for t in self.left_types)
            return f"{self.name}[{left_str}]"
        elif self.right_types:
            right_str = ", ".join(t.formatthis() for t in self.right_types)
            return f"{self.name}[-> {right_str}]"
        else:
            return f"{self.name}"


@dataclass(frozen=True)
class AnonymousGeneric(VType):
    identifier: int

    def toString(self) -> str:
        return f"@{self.identifier}"


@dataclass(frozen=True)
class ErrorType(VType):
    pass

    def toString(self) -> str:
        return "Error"


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
