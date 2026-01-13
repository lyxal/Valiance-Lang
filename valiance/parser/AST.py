from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence, Tuple


from valiance.lexer.Token import Token
from valiance.compiler_common.Location import Location
from valiance.compiler_common.TagCategories import TagCategory
from valiance.vtypes.VTypes import ElementTag, VType
from valiance.compiler_common.Identifier import Identifier, StaticIndex


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


class Visibility(Enum):
    PUBLIC = "public"
    READABLE = "readable"  # default
    PRIVATE = "private"


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


@dataclass(frozen=True, repr=False)
class LiteralNode(ASTNode):
    """Represents a literal value"""

    value: str
    type_: VType

    def __repr__(self):
        return f"{self.value} [{self.type_.formatthis()}]"


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
    element_tags: list[ElementTag]
    parameters: list[Parameter]
    output: list[VType]
    body: ASTNode
    visibility: Visibility = (
        Visibility.PUBLIC
    )  # 9 times out of 10 this will never be set


@dataclass(frozen=True)
class VariantNode(ASTNode):
    """Represents a variant (sealed trait with exhaustive set of implementations).

    Unlike traits (open-world), variants are closed-world:
    - Only objects defined inside can implement the variant
    - Enables exhaustive pattern matching
    - Objects automatically become subtypes of the variant
    """

    generics: list[VType]
    name: Identifier

    # Trait-like method requirements
    required_methods: list[DefineNode]  # Empty bodies - must be implemented
    default_methods: list[DefineNode]  # With bodies - can be overridden

    # Sealed set of implementations
    variant_objects: list[ObjectDefinitionNode]  # Objects defined inside

    @property
    def variant_type_names(self) -> list[str]:
        """Get names of all variant cases for exhaustiveness checking"""
        return [obj.object_name.name for obj in self.variant_objects]


@dataclass(frozen=True)
class FieldNode(ASTNode):
    """Represents an object field (must be set by constructor)"""

    visibility: Visibility
    name: Identifier
    type_: VType


@dataclass(frozen=True)
class MemberNode(ASTNode):
    """Represents an object member (must be given initial value at definition)"""

    visibility: Visibility
    name: Identifier
    value: ASTNode


@dataclass(frozen=True)
class ObjectDefinitionNode(ASTNode):
    """Base object definition"""

    generics: list[VType]
    object_name: Identifier
    fields: list[
        FieldNode
    ]  # Must be set by either default constructor or sub-constructors
    members: list[MemberNode]  # Given a default value by the object.
    default_constructor: list[tuple[FieldNode, Optional[ASTNode]]] | None
    methods: list[DefineNode]


@dataclass(frozen=True)
class ObjectTraitImplNode(ASTNode):
    """Trait implementation for an object"""

    generics: list[VType]
    object_name: Identifier
    trait: VType
    methods: list[DefineNode]


@dataclass(frozen=True)
class TraitNode(ASTNode):
    """Represents a trait definition"""

    generics: list[VType]
    name: Identifier
    # Separate required and default explicitly
    required_methods: list[DefineNode]  # Empty bodies
    default_methods: list[DefineNode]  # With implementations


@dataclass(frozen=True)
class TraitImplTraitNode(ASTNode):
    """Trait implementation for a trait (trait inheritance)"""

    generics: list[VType]
    trait_name: Identifier
    parent_trait: VType

    required_methods: list[DefineNode]
    default_methods: list[DefineNode]


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
class QuotedFunctionNode(ASTNode):
    """Represents a quoted element"""

    element: ASTNode


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


@dataclass(frozen=True)
class AliasedImportNode(ASTNode):
    """Represents an aliased import statement"""

    module_name: Identifier
    alias: Identifier


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


class MatchBranch:
    body: ASTNode


class MatchExactBranch(MatchBranch):
    def __init__(self, values: list[ASTNode]):
        self.values = values


class MatchIfBranch(MatchBranch):
    def __init__(self, condition: ASTNode):
        self.condition = condition


class MatchPatternBranch(MatchBranch):
    def __init__(self, pattern: MatchPattern, predicate: ASTNode | None = None):
        self.pattern = pattern
        self.predicate = predicate


# A pattern component class to represent the different parts of a pattern


@dataclass(frozen=True)
class PatternComponent(ABC):
    pass


@dataclass(frozen=True)
class ASTComponent(PatternComponent):
    node: ASTNode


@dataclass(frozen=True)
class WildcardComponent(PatternComponent):
    name: Identifier | None


@dataclass(frozen=True)
class GreedyComponent(PatternComponent):
    name: Identifier | None


# A pattern class to represent different types of patterns
@dataclass(frozen=True)
class MatchPattern(ABC):
    pass


@dataclass(frozen=True)
class StringPattern(MatchPattern):
    value: ASTNode


@dataclass(frozen=True)
class ListPattern(MatchPattern):
    elements: Sequence[PatternComponent]


@dataclass(frozen=True)
class TuplePattern(MatchPattern):
    elements: Sequence[PatternComponent]


@dataclass(frozen=True)
class ErrorPattern(MatchPattern):
    """Represents an error in pattern matching"""

    pass


class MatchAsBranch(MatchBranch):
    def __init__(
        self,
        name: Identifier | None,
        type_: VType | None,
        predicate: ASTNode | None = None,
    ):
        if name is None and type_ is None:
            raise ValueError(
                "At least one of name or type_ must be provided for MatchAsBranch"
            )
        self.name = name
        self.type_ = type_
        self.predicate = predicate


class MatchDefaultBranch(MatchBranch):
    pass


@dataclass(frozen=True)
class MatchNode(ASTNode):
    """Represents a match operation with multiple branches"""

    branches: list[MatchBranch]


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

    parameters: list[Parameter] | None
    condition: ASTNode
    body: ASTNode


@dataclass(frozen=True)
class ForNode(ASTNode):
    """Represents a for loop operation"""

    iterator: Identifier
    index: Identifier | None
    body: ASTNode


@dataclass(frozen=True)
class UnfoldNode(ASTNode):
    """Represents an unfold operation"""

    parameters: list[Parameter] | None
    condition: ASTNode
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

    indices: list[StaticIndex]
    dump: bool = False


class OverlayRule:
    def __init__(
        self,
        element: Identifier,
        generics: list[VType],
        arguments: list[VType],
        returns: list[VType],
    ):
        self.element = element
        self.generics = generics
        self.arguments = arguments
        self.returns = returns


@dataclass(frozen=True)
class TagCreationNode(ASTNode):
    tag_name: Identifier
    category: TagCategory
    rules: list[OverlayRule]


@dataclass(frozen=True)
class TagExtendNode(ASTNode):
    tag_name: Identifier
    rules: list[OverlayRule]


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


@dataclass(frozen=True)
class BreakNode(ASTNode):
    """Represents a break operation in loops"""

    values: list[ASTNode] | None
