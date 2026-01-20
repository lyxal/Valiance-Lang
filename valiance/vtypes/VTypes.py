from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import enum
from typing import Callable, Tuple

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


@dataclass(kw_only=True)
class VType(ABC):
    data_tags: tuple[DataTag, ...] = field(default_factory=tuple)
    element_tags: tuple[ElementTag, ...] = field(default_factory=tuple)

    non_vectorising: bool = False  # Indicates if the type is non-vectorising
    is_base_type: bool = False  # Indicates if the type is a base type

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

        # Indicate non-vectorising with "(non-vectorising)" if applicable
        if self.non_vectorising:
            element_tags_str = "(non-vectorising) " + element_tags_str

        # Indicate base type with "(base type)" if applicable
        if self.is_base_type:
            element_tags_str = "(base type) " + element_tags_str

        return f"{data_tags_str} {self.toString()} {element_tags_str}".strip()


@dataclass()
class NumberType(VType):
    pass

    def toString(self) -> str:
        return "Number"


@dataclass()
class StringType(VType):
    pass

    def toString(self) -> str:
        return "String"


@dataclass()
class ListType(VType):
    element_type: VType
    rank: (
        int | str
    )  # int if rank is expressed as numbers, str if it's depedent on where

    def toString(self) -> str:
        rank_str = str("~" * self.rank) if isinstance(self.rank, int) else self.rank
        return f"{self.element_type.formatthis()}{rank_str}"


@dataclass()
class MinimumRankType(ListType):
    element_type: VType

    def toString(self) -> str:
        rank_str = str("*" * self.rank) if isinstance(self.rank, int) else self.rank
        return f"{self.element_type.formatthis()}{rank_str}+"


@dataclass()
class ExactRankType(ListType):
    element_type: VType

    def toString(self) -> str:
        rank_str = str("+" * self.rank) if isinstance(self.rank, int) else self.rank
        return f"{self.element_type.formatthis()}{rank_str}"


@dataclass()
class UnionType(VType):
    left: VType
    right: VType

    def toString(self) -> str:
        return f"({self.left.formatthis()} | {self.right.formatthis()})"


@dataclass()
class IntersectionType(VType):
    left: VType
    right: VType

    def toString(self) -> str:
        return f"({self.left.formatthis()} & {self.right.formatthis()})"


@dataclass()
class OptionalType(VType):
    base_type: VType

    def toString(self) -> str:
        return f"{self.base_type.formatthis()}?"


@dataclass()
class TupleType(VType):
    element_types: list[VType]

    def toString(self) -> str:
        element_types_str = ", ".join(t.formatthis() for t in self.element_types)
        return f"({element_types_str})"


@dataclass()
class DictionaryType(VType):
    key_type: VType
    value_type: VType

    def toString(self) -> str:
        return f"Dictionary[{self.key_type.formatthis()} -> {self.value_type.formatthis()}]"


@dataclass()
class FunctionType(VType):
    fully_typed: bool
    generics: list[VType]
    param_types: list[VType]
    return_types: list[VType]
    where_clauses: list[str]  # Placeholder for where clauses

    def toString(self) -> str:
        param_types_str = ", ".join(t.formatthis() for t in self.param_types)
        return_types_str = ", ".join(t.formatthis() for t in self.return_types)
        return f"Function[{param_types_str} -> {return_types_str}]"


@dataclass()
class CustomType(VType):
    name: Identifier
    left_types: list[VType]
    right_types: list[VType]
    traits: tuple[Identifier] = field(default_factory=lambda: tuple[Identifier]())

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


@dataclass()
class AnonymousGeneric(VType):
    identifier: int

    def toString(self) -> str:
        return f"@{self.identifier}"


@dataclass()
class ErrorType(VType):
    pass

    def toString(self) -> str:
        return "Error"


@dataclass
class Overload:
    params: list[VType]
    returns: list[VType]
    arity: int
    multiplicity: int

    def fits(self, stack: list[VType]) -> bool:
        for expected, actual in zip(
            reversed(self.params), reversed(stack[-self.arity :])
        ):
            if not type_compatible(expected, actual):
                return False
        return True


@dataclass
class ObjectDef:
    generics: list[Identifier]
    members: dict[Identifier, VType]
    traits: list[Identifier]


@dataclass
class TraitDef:
    generics: list[Identifier]
    required_methods: list[Overload]


@dataclass
class InferenceTypeVariable(VType):
    _id: int

    def toString(self) -> str:
        return f"T{self._id}"


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


def type_compatible(expected: VType, actual: VType) -> bool:
    return specificity_level(expected, actual) != -1


class Specificity(enum.Enum):
    LEFT = 1
    RIGHT = 2
    NEITHER = 3


def choose_overload(overload_set: list[Overload], stack: list[VType]) -> Overload:
    best = overload_set[0]
    for candidate in overload_set[1:]:
        comparison = compare_specificity(best, candidate, stack)
        if comparison == Specificity.RIGHT:
            best = candidate
        elif comparison == Specificity.NEITHER:
            raise ValueError("Ambiguous overloads found during type checking")
    return best


def compare_specificity(
    overload_a: Overload, overload_b: Overload, stack: list[VType]
) -> Specificity:
    spec = None
    for arg_a, arg_b, actual in zip(
        reversed(overload_a.params),
        reversed(overload_b.params),
        reversed(stack[-overload_a.arity :]),
    ):
        level_of_a = specificity_level(arg_a, actual)
        level_of_b = specificity_level(arg_b, actual)

        assert level_of_a != -1 and level_of_b != -1  # Both must be compatible
        # Ideally this will be ensured by the caller, but just in case

        # If `spec` is None, that means it hasn't been set yet
        # otherwise, it means there is already a specificity determined
        # and that the new comparison must not conflict with it

        # If there is a conflict, return NEITHER immediately
        if level_of_a < level_of_b:
            spec = Specificity.LEFT if spec is None else None
        elif level_of_b < level_of_a:
            spec = Specificity.RIGHT if spec is None else None

        if spec is None:  # Conflict in specificity
            return Specificity.NEITHER
    return spec if spec is not None else Specificity.NEITHER


# Note that in all of these functions, expected = the overload parameter type,
# and actual = the type on the stack being compared against


def specificity_level(expected: VType, actual: VType) -> int:
    # Lower is more specific
    RULES: list[Callable[[VType, VType], bool]] = [
        exact_match,
        lambda e, a: isinstance(e, OptionalType) and exact_match(e.base_type, a),
        e_vectorises_over_a,
        intersection_match,
        trait_implementation_match,
        rank_subsumption,
        union_match,
    ]

    # Find index of first rule that matches
    for index, rule in enumerate(RULES):
        if rule(expected, actual):
            return index
    return -1  # No match found, so return an invalid level


def exact_match(expected: VType, actual: VType) -> bool:
    return type(expected) == type(actual) and expected == actual


def e_vectorises_over_a(expected: VType, actual: VType) -> bool:
    if not isinstance(actual, ListType):
        # If actual isn't a list, then there's 0 way it can vectorise over expected
        return False
    if isinstance(expected, ListType):
        # First, check if the base types are even compatible
        if not type_compatible(expected.element_type, actual.element_type):
            return False
        # Then check if rank(actual) > rank(expected)
        # note that if either rank is dependent (i.e. str), no vectorisation can be
        # assumed
        if isinstance(expected.rank, int) and isinstance(actual.rank, int):
            return actual.rank > expected.rank
        return False
    else:
        # A list passed where a scalar expected always vectorises
        # UNLESS expected is non-vectorising
        return expected.non_vectorising


def intersection_match(expected: VType, actual: VType) -> bool:
    if not isinstance(actual, IntersectionType):
        return False
    return type_compatible(expected, actual.left) and type_compatible(
        expected, actual.right
    )


def trait_implementation_match(expected: VType, actual: VType) -> bool:
    if not isinstance(expected, CustomType):
        return False
    if not expected.traits:
        return False
    if not isinstance(actual, CustomType):
        return False
    for trait in expected.traits:
        if trait not in actual.traits:
            return False
    return True


def rank_subsumption(expected: VType, actual: VType) -> bool:
    # First, check if both are ListTypes
    if not isinstance(expected, ListType) or not isinstance(actual, ListType):
        return False

    # And check if their element types are compatible
    if not type_compatible(expected.element_type, actual.element_type):
        return False

    # Check that the ranks are equal. Higher actual rank should have been caught
    # by e_vectorises_over_a
    if expected.rank != actual.rank:
        return False

    assert expected.rank == actual.rank  # Just for now, a little assert
    # to catch the cases where my reasoning is wrong.

    # The only case rank subsumption does not apply is when
    # expected is Exact/Minimum and actual is Rugged.

    if isinstance(expected, (ExactRankType, MinimumRankType)) and not isinstance(
        actual, (ExactRankType, MinimumRankType)
    ):
        return False

    return True


def union_match(expected: VType, actual: VType) -> bool:
    if not isinstance(actual, UnionType):
        return False
    return type_compatible(expected, actual.left) or type_compatible(
        expected, actual.right
    )
