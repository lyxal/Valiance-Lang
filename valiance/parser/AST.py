from typing import Tuple


class ASTNode:
    """Base class for all AST nodes."""

    pass


class GroupNode(ASTNode):
    """Represents a group of elements"""

    def __init__(self, elements: list[ASTNode]):
        self.elements = elements


class ElementNode(ASTNode):
    """Represents a normal element"""

    def __init__(self, element_name: str, modified: bool = False):
        self.element_name = element_name
        self.modified = modified


class TupleNode(ASTNode):
    """Represents a tuple of elements"""

    def __init__(self, elements: list[ASTNode]):
        self.elements = elements


class TypeNode(ASTNode):
    """Represents a type"""

    def __init__(self, type_: str):
        self.type_ = type_


class DefineNode(ASTNode):
    """Represents a definition of an element or tuple"""

    def __init__(
        self,
        generics: list[TypeNode],
        name: str,
        parameters: list[Tuple[str, TypeNode]],
        output: list[TypeNode],
        body: GroupNode,
    ):
        self.generics = generics
        self.name = name
        self.parameters = parameters
        self.output = output
        self.body = body


class VariantNode(ASTNode):
    """Represents a variant type with multiple options"""

    def __init__(self, options: list[ObjectNode]):
        self.options = options


class ObjectNode(ASTNode):
    """Represents an object definition with generics, name, implemented traits, and body"""

    def __init__(
        self,
        generics: list[TypeNode],
        name: str,
        implemented_traits: list[TypeNode],
        body: GroupNode,
    ):
        self.generics = generics
        self.name = name
        self.implemented_traits = implemented_traits
        self.body = body


class TraitNode(ASTNode):
    """Represents a trait definition with generics, name, other traits, and body"""

    def __init__(
        self,
        generics: list[TypeNode],
        name: str,
        other_traits: list[TypeNode],
        body: GroupNode,
    ):
        self.generics = generics
        self.name = name
        self.other_traits = other_traits
        self.body = body


class ListNode(ASTNode):
    """Represents a list of elements"""

    def __init__(self, items: list[ASTNode]):
        self.items = items


class FunctionNode(ASTNode):
    """Represents a function/lambda expression"""

    def __init__(
        self,
        parameters: list[Tuple[str, TypeNode]],
        output: list[TypeNode],
        body: GroupNode,
    ):
        self.parameters = parameters
        self.output = output
        self.body = body


class VariableGetNode(ASTNode):
    """Represents a variable retrieval"""

    def __init__(self, name: str):
        self.name = name


class VariableSetNode(ASTNode):
    """Represents a variable assignment"""

    def __init__(self, name: str, value: GroupNode):
        self.name = name
        self.value = value


class DuplicateNode(ASTNode):
    """Represents the dup operation, labels optional"""

    def __init__(self, prestack: list[str], poststack: list[str]):
        self.prestack = prestack if prestack is not [] else ["a"]
        self.poststack = poststack if poststack is not [] else ["a"]


class SwapNode(ASTNode):
    """Represents the swap operation, labels optional"""

    def __init__(self, prestack: list[str], poststack: list[str]):
        self.prestack = prestack if prestack is not [] else ["a", "b"]
        self.poststack = poststack if poststack is not [] else ["b", "a"]


class ModuleImportNode(ASTNode):
    """Represents a module import statement"""

    def __init__(self, module_name: str, components: list[str]):
        self.module_name = module_name
        self.components = components


class AliasedImportNode(ASTNode):
    """Represents an aliased import statement"""

    def __init__(self, original_name: str, alias_name: str):
        self.original_name = original_name
        self.alias_name = alias_name


class ConstantSetNode(ASTNode):
    """Represents a constant set operation"""

    def __init__(self, name: str, value: GroupNode):
        self.name = name
        self.value = value


class TypeCastNode(ASTNode):
    """Represents a type cast operation"""

    def __init__(self, target_type: TypeNode):
        self.target_type = target_type


class IfNode(ASTNode):
    """Represents a single block if-conditional statement"""

    def __init__(self, condition: GroupNode, then_branch: GroupNode):
        self.condition = condition
        self.then_branch = then_branch


class BranchNode(ASTNode):
    """Represents a branch operation - if with mandatory else"""

    def __init__(
        self, condition: GroupNode, then_branch: GroupNode, else_branch: GroupNode
    ):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch


class MatchNode(ASTNode):
    """Represents a match operation with multiple branches"""

    def __init__(self, branches: list[Tuple[GroupNode, GroupNode]]):
        self.branches = branches


class AssertNode(ASTNode):
    """Represents an assert operation"""

    def __init__(self, condition: GroupNode):
        self.condition = condition


class AssertElseNode(ASTNode):
    """Represents an assert-else operation"""

    def __init__(self, condition: GroupNode, else_branch: GroupNode):
        self.condition = condition
        self.else_branch = else_branch


class WhileNode(ASTNode):
    """Represents a while loop operation"""

    def __init__(self, condition: GroupNode, body: GroupNode):
        self.condition = condition
        self.body = body


class ForNode(ASTNode):
    """Represents a for loop operation"""

    def __init__(self, iterator: str, body: GroupNode):
        self.iterator = iterator
        self.body = body


class AtNode(ASTNode):
    """Represents an at expression with levels"""

    def __init__(self, levels: list[Tuple[str, int]]):
        self.levels = levels
