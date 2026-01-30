from abc import abstractmethod
from compiler_common.Identifier import Identifier
from types.Tag import Tag


class Type:
    def __init__(self):
        self.tags: list[Tag] = []

    def add_tag(self, tag: Tag):
        self.tags.append(tag)

    def has_tag(self, tag_type: type) -> bool:
        return any(isinstance(tag, tag_type) for tag in self.tags)

    def without_tags(self) -> "Type":
        new_type = self.__class__.__new__(self.__class__)
        new_type.__dict__ = self.__dict__.copy()
        new_type.tags = []
        return new_type

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Type):
            return False
        return self.tags == other.tags and self.structural_eq(other)

    @abstractmethod
    def structural_eq(self, other: object) -> bool:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


class SimpleType(Type):
    def __init__(
        self,
        name: Identifier,
        left_generics: list["Type"] | None = None,
        right_generics: list["Type"] | None = None,
    ):
        super().__init__()
        self.name = name
        self.left_generics = left_generics if left_generics is not None else []
        self.right_generics = right_generics if right_generics is not None else []

    def structural_eq(self, other: object) -> bool:
        if not isinstance(other, SimpleType):
            return False
        return (
            self.name == other.name
            and self.left_generics == other.left_generics
            and self.right_generics == other.right_generics
        )

    def __str__(self) -> str:
        return str(self.name)


NUMBER_TYPE = lambda: SimpleType(Identifier(name="Number"))
STRING_TYPE = lambda: SimpleType(Identifier(name="String"))


class TupleType(Type):
    def __init__(self, element_types: list[Type]):
        super().__init__()
        self.element_types = element_types

    def structural_eq(self, other: object) -> bool:
        if not isinstance(other, TupleType):
            return False
        return self.element_types == other.element_types

    def __str__(self) -> str:
        return "tuple"


class Rank:
    def __init__(self, value: int | str):
        self.value = value

    def __lt__(self, other: "Rank") -> bool:
        if isinstance(self.value, int) and isinstance(other.value, int):
            return self.value < other.value
        raise TypeError("Cannot compare rank of dependent types")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Rank):
            return False
        return self.value == other.value

    def __gt__(self, other: "Rank") -> bool:
        if isinstance(self.value, int) and isinstance(other.value, int):
            return self.value > other.value
        raise TypeError("Cannot compare rank of dependent types")

    def __str__(self) -> str:
        return str(self.value)


class ListType(Type):
    def __init__(self, element_type: Type, rank: Rank):
        self.element_type: Type = element_type
        self.rank: Rank = rank
        super().__init__()

    def structural_eq(self, other: object) -> bool:
        if not isinstance(other, ListType):
            return False
        if type(self) is not type(other):
            return False
        return self.element_type == other.element_type and self.rank == other.rank

    def __str__(self) -> str:
        this_list_type = self.__class__.__name__
        return f"{this_list_type} of {self.element_type} with rank {self.rank}"


# A T~ type list
class RuggedList(ListType):
    pass


# A T+ type list
class ExactList(ListType):
    pass


# A T* type list
class MinimumList(ListType):
    pass


class UnionType(Type):
    def __init__(self, *types: Type):
        super().__init__()
        self.types = types

    def structural_eq(self, other: object) -> bool:
        if not isinstance(other, UnionType):
            return False
        return set(self.types) == set(other.types)

    def __str__(self) -> str:
        return " | ".join(str(t) for t in self.types)


class IntersectionType(Type):
    def __init__(self, *types: Type):
        super().__init__()
        self.types = types

    def structural_eq(self, other: object) -> bool:
        if not isinstance(other, IntersectionType):
            return False
        return set(self.types) == set(other.types)

    def __str__(self) -> str:
        return " & ".join(str(t) for t in self.types)


class OptionalType(Type):
    def __init__(self, base_type: Type):
        super().__init__()
        self.base_type = base_type

    def structural_eq(self, other: object) -> bool:
        if not isinstance(other, OptionalType):
            return False
        return self.base_type == other.base_type

    def __str__(self) -> str:
        return f"{self.base_type}?"


class AnonymousGenericType(Type):
    def __init__(self, _id: int):
        super().__init__()
        self._id = _id

    def structural_eq(self, other: object) -> bool:
        if not isinstance(other, AnonymousGenericType):
            return False
        return self._id == other._id

    def __str__(self) -> str:
        return f"@{self._id}"


class Error(Type):
    pass
