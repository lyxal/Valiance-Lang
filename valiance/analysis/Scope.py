from parser.AST import ASTNode, DefineNode
from valiance.compiler_common.Identifier import Identifier
from valiance.vtypes.VTypes import ObjectDef, Overload, TraitDef, VType


class Scope:
    def __init__(self, parent: Scope | None = None):
        self.parent = parent
        self.variables: dict[Identifier, VType] = {}
        self.partial_variables: dict[Identifier, ASTNode] = {}
        self.elements: dict[Identifier, list[Overload]] = {}
        self.definitions: dict[Identifier, list[DefineNode]] = {}
        self.objects: dict[Identifier, ObjectDef] = {}
        self.traits: dict[Identifier, TraitDef] = {}


class ScopeStack:
    def __init__(self):
        self.scopes: list[Scope] = [Scope()]

    def enter(self):
        new_scope = Scope(parent=self.scopes[-1])
        self.scopes.append(new_scope)

    def leave(self):
        self.scopes.pop()

    # Queries (search from innermost to outermost)
    def lookup_variable(self, name: Identifier) -> VType | None:
        for scope in reversed(self.scopes):
            if name in scope.variables:
                return scope.variables[name]
        return None

    def lookup_partial_variable(self, name: Identifier) -> ASTNode | None:
        for scope in reversed(self.scopes):
            if name in scope.partial_variables:
                return scope.partial_variables[name]
        return None

    def lookup_element(self, name: Identifier) -> list[Overload]:
        for scope in reversed(self.scopes):
            if name in scope.elements:
                return scope.elements[name]
        return []

    def lookup_definition(self, name: Identifier) -> list[DefineNode] | None:
        for scope in reversed(self.scopes):
            if name in scope.definitions:
                return scope.definitions[name]
        return None

    def lookup_object(self, name: Identifier) -> ObjectDef | None:
        for scope in reversed(self.scopes):
            if name in scope.objects:
                return scope.objects[name]
        return None

    def lookup_trait(self, name: Identifier) -> TraitDef | None:
        for scope in reversed(self.scopes):
            if name in scope.traits:
                return scope.traits[name]
        return None

    # Mutations (add to current/innermost scope)
    def declare_variable(self, name: Identifier, ty: VType):
        self.scopes[-1].variables[name] = ty

    def add_partial_variable(self, name: Identifier, value: ASTNode):
        self.scopes[-1].partial_variables[name] = value

    def add_overload(self, name: Identifier, overload: Overload):
        if name not in self.scopes[-1].elements:
            self.scopes[-1].elements[name] = []
        self.scopes[-1].elements[name].append(overload)

    def add_definition(self, name: Identifier, definition: DefineNode):
        if name not in self.scopes[-1].definitions:
            self.scopes[-1].definitions[name] = []
        self.scopes[-1].definitions[name].append(definition)

    def add_object(self, name: Identifier, obj: ObjectDef):
        self.scopes[-1].objects[name] = obj

    def add_object_trait(self, name: Identifier, trait: Identifier):
        self.scopes[-1].objects[name].traits.append(trait)

    def add_trait(self, name: Identifier, trait: TraitDef):
        self.scopes[-1].traits[name] = trait
