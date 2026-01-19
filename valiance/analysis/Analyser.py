from valiance.analysis.Scope import Scope
from valiance.analysis.ScopeController import ScopeController
from valiance.parser.AST import (
    ASTNode,
    DefineNode,
    ElementNode,
    ListNode,
    LiteralNode,
    ObjectDefinitionNode,
    TraitNode,
)
from valiance.compiler_common.Primitives import PRIMITIVES


class Analyser:
    def __init__(self, asts: list[ASTNode]):
        self.asts = asts
        self.scope_controller = ScopeController()

        for primitive_ident, overloads in PRIMITIVES.items():
            self.scope_controller.elements[primitive_ident] = overloads

    def analyse(self) -> list[list[Scope]]:
        # 1. Name Collection
        for ast in self.asts:
            match ast:
                case DefineNode():
                    self.scope_controller.register_element(ast.name, ast)
                case ObjectDefinitionNode():
                    self.scope_controller.register_object(ast.object_name, ast)
                case TraitNode():
                    self.scope_controller.register_trait(ast.name, ast)
                case _:
                    continue

        # 2. Type Checking
        for ast in self.asts:
            match ast:
                case LiteralNode():
                    self.scope_controller.push(ast.type_)
                case ListNode():
                    self.scope_controller.push_type_of(ast)
                case ElementNode():
                    overloads = self.scope_controller.get_element(ast.element_name)
                    if overloads is None:
                        raise ValueError(
                            f"Element {ast.element_name.name} not found in scope"
                        )
                    self.scope_controller.apply(overloads)
                case _:
                    raise NotImplementedError(
                        f"Type checking for ASTNode of type {type(ast)} not implemented"
                    )

        return list(self.scope_controller.scopes)
