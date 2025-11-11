from dataclasses import dataclass
from typing import Sequence, Tuple
from abc import ABC

from valiance.vtypes.VTypes import VType


@dataclass(frozen=True)
class ASTNode(ABC):
    """Base class for all AST nodes. Sealed via explicit subclass enumeration."""

    pass


@dataclass(frozen=True)
class GroupNode(ASTNode):
    """Represents a group of elements"""

    elements: Sequence[ASTNode]


@dataclass(frozen=True)
class ElementNode(ASTNode):
    """Represents a normal element"""

    element_name: str
    generics: list[VType]
    args: list[Tuple[str, ASTNode]]
    modified: bool = False


@dataclass(frozen=True)
class LiteralNode(ASTNode):
    """Represents a literal value"""

    value: str
    type_: VType


@dataclass(frozen=True)
class TupleNode(ASTNode):
    """Represents a tuple of elements"""

    elements: Sequence[ASTNode]


@dataclass(frozen=True)
class TypeNode(ASTNode):
    """Represents a type"""

    type_: str


@dataclass(frozen=True)
class DefineNode(ASTNode):
    """Represents a definition of an element or tuple"""

    generics: list[TypeNode]
    name: str
    parameters: list[Tuple[str, TypeNode]]
    output: list[TypeNode]
    body: GroupNode


@dataclass(frozen=True)
class VariantNode(ASTNode):
    """Represents a variant type with multiple options"""

    options: list["ObjectNode"]


@dataclass(frozen=True)
class ObjectNode(ASTNode):
    """Represents an object definition with generics, name, implemented traits, and body"""

    generics: list[TypeNode]
    name: str
    implemented_traits: list[TypeNode]
    body: GroupNode


@dataclass(frozen=True)
class TraitNode(ASTNode):
    """Represents a trait definition with generics, name, other traits, and body"""

    generics: list[TypeNode]
    name: str
    other_traits: list[TypeNode]
    body: GroupNode


@dataclass(frozen=True)
class ListNode(ASTNode):
    """Represents a list of elements"""

    items: Sequence[ASTNode]


@dataclass(frozen=True)
class FunctionNode(ASTNode):
    """Represents a function/lambda expression"""

    parameters: list[Tuple[str, TypeNode]]
    output: list[TypeNode]
    body: GroupNode


@dataclass(frozen=True)
class VariableGetNode(ASTNode):
    """Represents a variable retrieval"""

    name: str


@dataclass(frozen=True)
class VariableSetNode(ASTNode):
    """Represents a variable assignment"""

    name: str
    value: ASTNode


@dataclass(frozen=True)
class AugmentedVariableSetNode(ASTNode):
    """Represents an augmented variable assignment"""

    name: str
    function: ASTNode


@dataclass(frozen=True)
class DuplicateNode(ASTNode):
    """Represents the dup operation, labels optional"""

    prestack: list[str]
    poststack: list[str]

    def __post_init__(self):
        # Handle default values for empty lists
        if not self.prestack:
            object.__setattr__(self, "prestack", ["a"])
        if not self.poststack:
            object.__setattr__(self, "poststack", ["a"])


@dataclass(frozen=True)
class SwapNode(ASTNode):
    """Represents the swap operation, labels optional"""

    prestack: list[str]
    poststack: list[str]

    def __post_init__(self):
        # Handle default values for empty lists
        if not self.prestack:
            object.__setattr__(self, "prestack", ["a", "b"])
        if not self.poststack:
            object.__setattr__(self, "poststack", ["b", "a"])


@dataclass(frozen=True)
class ModuleImportNode(ASTNode):
    """Represents a module import statement"""

    module_name: str
    components: list[str]


@dataclass(frozen=True)
class AliasedImportNode(ASTNode):
    """Represents an aliased import statement"""

    original_name: str
    alias_name: str


@dataclass(frozen=True)
class ConstantSetNode(ASTNode):
    """Represents a constant set operation"""

    name: str
    value: GroupNode


@dataclass(frozen=True)
class TypeCastNode(ASTNode):
    """Represents a type cast operation"""

    target_type: TypeNode


@dataclass(frozen=True)
class IfNode(ASTNode):
    """Represents a single block if-conditional statement"""

    condition: GroupNode
    then_branch: GroupNode


@dataclass(frozen=True)
class BranchNode(ASTNode):
    """Represents a branch operation - if with mandatory else"""

    condition: GroupNode
    then_branch: GroupNode
    else_branch: GroupNode


@dataclass(frozen=True)
class MatchNode(ASTNode):
    """Represents a match operation with multiple branches"""

    branches: list[Tuple[GroupNode, GroupNode]]


@dataclass(frozen=True)
class AssertNode(ASTNode):
    """Represents an assert operation"""

    condition: GroupNode


@dataclass(frozen=True)
class AssertElseNode(ASTNode):
    """Represents an assert-else operation"""

    condition: GroupNode
    else_branch: GroupNode


@dataclass(frozen=True)
class WhileNode(ASTNode):
    """Represents a while loop operation"""

    condition: GroupNode
    body: GroupNode


@dataclass(frozen=True)
class ForNode(ASTNode):
    """Represents a for loop operation"""

    iterator: str
    body: GroupNode


@dataclass(frozen=True)
class AtNode(ASTNode):
    """Represents an at expression with levels"""

    levels: list[Tuple[str, int]]
