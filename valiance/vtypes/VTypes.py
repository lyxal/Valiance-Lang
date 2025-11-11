from abc import ABC
from dataclasses import dataclass


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
class CustomType(VType):
    name: str
