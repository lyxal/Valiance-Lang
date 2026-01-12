from dataclasses import dataclass

from valiance.parser.AST import FieldNode
from valiance.vtypes.VTypes import ElementTag, VType


@dataclass(frozen=True)
class Symbol:
    pass


@dataclass(frozen=True)
class DefineSymbol(Symbol):
    generics: list[VType]
    element_tags: list[ElementTag]
    parameters: list[VType]
    outputs: list[VType]


@dataclass(frozen=True)
class VariableSymbol(Symbol):
    type_: VType | None  # None if type is to be inferred


@dataclass(frozen=True)
class ObjectSymbol(Symbol):
    fields: list[FieldNode]
    # Don't make methods a part of this symbol
    # because each method should have its own DefineSymbol
    # added to the symbol table separately.
    generics: list[VType]
