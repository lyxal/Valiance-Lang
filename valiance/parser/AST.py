from abc import ABC
from dataclasses import dataclass
from typing import Sequence, Tuple

from valiance.compiler_common.Identifier import Identifier
from valiance.lexer.Token import Token
from valiance.compiler_common.Location import Location
from valiance.compiler_common.Index import Index
from valiance.compiler_common.TagCategories import TagCategory
from valiance.vtypes.VTypes import ElementTag, VType


class Parameter:
    def __init__(
        self,
        name: Identifier,
        type_: VType,
        cast: VType | None = None,
        default: ASTNode | None = None,
    ):
        self.name = name
        self.type_ = type_
        self.cast = cast
        self.default = default

    def __repr__(self):
        return f"Parameter(name = {self.name}, type = {self.type_}, cast = {self.cast}, default = {self.default})"


@dataclass(frozen=True)
class ASTNode(ABC):
    """Base class for all AST nodes. Sealed via explicit subclass enumeration."""

    location: Location
    pass


@dataclass(frozen=True)
class ErrorNode(ASTNode):
    """Represents an error in the AST"""

    token: Token

    def __repr__(self):
        return f"{self.token.value}"


@dataclass(frozen=True)
class AuxiliaryNode(ASTNode):
    """Used for parsing purposes only; should not appear in final AST"""

    pass


@dataclass(frozen=True)
class AuxiliaryTokenNode(AuxiliaryNode):
    """Holds a single token for auxiliary purposes"""

    token: Token


@dataclass(frozen=True)
class GroupNode(ASTNode):
    """Represents a group of elements"""

    elements: list[ASTNode]


@dataclass(frozen=True)
class ElementNode(ASTNode):
    """Represents a normal element"""

    element_name: Identifier
    generics: list[VType]
    args: list[Tuple[Identifier, ASTNode]]
    modifier_args: list[ASTNode]


@dataclass(frozen=True)
class ElementArgumentIgnoreNode(ASTNode):
    """Represents an argument to skip in an element call syntax"""


@dataclass(frozen=True)
class ElementArgumentFillNode(ASTNode):
    """Represents an argument to fill in an element call syntax.
    In other words, partial application with #
    """


@dataclass(frozen=True)
class LiteralNode(ASTNode):
    """Represents a literal value"""

    value: str
    type_: VType


@dataclass(frozen=True)
class TupleNode(ASTNode):
    """Represents a tuple of elements"""

    elements: Sequence[ASTNode]
    length: int


@dataclass(frozen=True)
class DictionaryNode(ASTNode):
    """Represents a dictionary of key-value pairs"""

    entries: list[Tuple[ASTNode, ASTNode]]


@dataclass(frozen=True)
class DefineNode(ASTNode):
    """Represents a definition of an element or tuple"""

    generics: list[VType]
    name: Identifier
    parameters: list[Tuple[Identifier, VType]]
    output: list[VType]
    body: ASTNode


@dataclass(frozen=True)
class VariantNode(ASTNode):
    """Represents a variant type with multiple options"""

    options: list["ObjectNode"]


@dataclass(frozen=True)
class ObjectNode(ASTNode):
    """Represents an object definition with generics, name, implemented traits, and body"""

    generics: list[VType]
    name: Identifier
    implemented_traits: list[VType]
    body: ASTNode


@dataclass(frozen=True)
class TraitNode(ASTNode):
    """Represents a trait definition with generics, name, other traits, and body"""

    generics: list[VType]
    name: Identifier
    other_traits: list[VType]
    body: ASTNode


@dataclass(frozen=True)
class ListNode(ASTNode):
    """Represents a list of elements"""

    items: Sequence[ASTNode]


@dataclass(frozen=True)
class FunctionNode(ASTNode):
    """Represents a function/lambda expression"""

    generics: list[VType]
    parameters: list[Parameter]
    output: list[VType]
    body: ASTNode
    element_tags: Tuple[ElementTag, ...] = tuple()


@dataclass(frozen=True)
class VariableGetNode(ASTNode):
    """Represents a variable retrieval"""

    name: Identifier


@dataclass(frozen=True)
class VariableSetNode(ASTNode):
    """Represents a variable assignment"""

    name: Identifier
    value: ASTNode


@dataclass(frozen=True)
class MultipleVariableSetNode(ASTNode):
    """Represents multiple variable assignment"""

    names: list[Identifier]
    value: ASTNode


@dataclass(frozen=True)
class AugmentedVariableSetNode(ASTNode):
    """Represents an augmented variable assignment"""

    name: Identifier
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
class PopNode(ASTNode):
    """Represents the pop operation, labels optional"""

    prestack: list[str]
    poststack: list[str]

    def __post_init__(self):
        # Handle default values for empty lists
        if not self.prestack:
            object.__setattr__(self, "prestack", ["a"])
        if self.poststack:
            raise ValueError("Poststack must be empty for PopNode")


@dataclass(frozen=True)
class ModuleImportNode(ASTNode):
    """Represents a module import statement"""

    module_name: Identifier
    components: list[Identifier]


@dataclass(frozen=True)
class AliasedImportNode(ASTNode):
    """Represents an aliased import statement"""

    original_name: Identifier
    alias_name: Identifier


@dataclass(frozen=True)
class ConstantSetNode(ASTNode):
    """Represents a constant set operation"""

    name: Identifier
    value: ASTNode


@dataclass(frozen=True)
class IfNode(ASTNode):
    """Represents a single block if-conditional statement"""

    condition: ASTNode
    then_branch: ASTNode
    else_branch: ASTNode | None


@dataclass(frozen=True)
class MatchNode(ASTNode):
    """Represents a match operation with multiple branches"""

    branches: list[Tuple[ASTNode, ASTNode]]


@dataclass(frozen=True)
class AssertNode(ASTNode):
    """Represents an assert operation"""

    condition: ASTNode


@dataclass(frozen=True)
class AssertElseNode(ASTNode):
    """Represents an assert-else operation"""

    condition: ASTNode
    else_branch: ASTNode


@dataclass(frozen=True)
class WhileNode(ASTNode):
    """Represents a while loop operation"""

    condition: ASTNode
    body: ASTNode


@dataclass(frozen=True)
class ForNode(ASTNode):
    """Represents a for loop operation"""

    iterator: Identifier
    body: ASTNode


@dataclass(frozen=True)
class UnfoldNode(ASTNode):
    """Represents an unfold operation"""

    body: ASTNode


@dataclass(frozen=True)
class TryHandleNode(ASTNode):
    """Represents a try-handle operation"""

    try_block: ASTNode
    handle_block: ASTNode


@dataclass(frozen=True)
class AtNode(ASTNode):
    """Represents an at expression with levels"""

    levels: list[Tuple[Identifier, int]]


@dataclass(frozen=True)
class IndexNode(ASTNode):
    """Represents an index dump operation"""

    indices: list[Index]
    dump: bool = False


@dataclass(frozen=True)
class TagDefinitionNode(ASTNode):
    """Represents a tag definition"""

    name: Identifier
    category: TagCategory


@dataclass(frozen=True)
class TagOverlayNode(ASTNode):
    """Represents a tag overlay operation"""

    name: Identifier
    # TODO: Figure out what goes here


@dataclass(frozen=True)
class TagDisjointNode(ASTNode):
    """Represents a tag disjoint operation"""

    parent_tag: Identifier
    child_tag: Identifier


@dataclass(frozen=True)
class AnnotationNode(ASTNode):
    """Represents an annotation operation"""

    annotation: Identifier
    target: ASTNode


@dataclass(frozen=True)
class PanicNode(ASTNode):
    """Represents a panic operation"""

    message: ASTNode


@dataclass(frozen=True)
class SpawnNode(ASTNode):
    """Represents a spawn operation"""

    body: ASTNode


@dataclass(frozen=True)
class ConcurrentBlockNode(ASTNode):
    """Represents a concurrent block operation"""

    body: ASTNode


@dataclass(frozen=True)
class MatchChannelsNode(ASTNode):
    """Represents a match-channels operation"""

    branches: list[Tuple[ASTNode, ASTNode]]


@dataclass(frozen=True)
class EnumNode(ASTNode):
    """Represents an enum definition"""

    name: Identifier
    variants: list[Tuple[Identifier, ASTNode]]


@dataclass(frozen=True)
class SafeTypeCastNode(ASTNode):
    """Represents a safe type cast operation"""

    target_type: VType


@dataclass(frozen=True)
class UnsafeTypeCastNode(ASTNode):
    """Represents an unsafe type cast operation"""

    target_type: VType
