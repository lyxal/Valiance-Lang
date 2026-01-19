from valiance.analysis.Scope import Scope
from valiance.compiler_common.Identifier import Identifier
from valiance.parser.AST import ASTNode, DefineNode, ObjectDefinitionNode, TraitNode
from valiance.vtypes.VTypes import ObjectDef, Overload, TraitDef, VType


class ScopeController:
    def __init__(self):
        self.variables: dict[Identifier, VType] = {}
        self.elements: dict[Identifier, list[Overload]] = {}
        self.objects: dict[Identifier, ObjectDef] = {}
        self.traits: dict[Identifier, TraitDef] = {}

        self.unchecked_elements: dict[Identifier, DefineNode] = {}
        self.unchecked_objects: dict[Identifier, ObjectDefinitionNode] = {}
        self.unchecked_traits: dict[Identifier, TraitNode] = {}

        self.scopes: list[list[Scope]] = [[Scope()]]

    def create_scope(self, inputs: list[VType] | None = None):
        if len(self.scopes) == 0:
            self.scopes.append([Scope(inputs=inputs)])
        else:
            new_scope = Scope(inputs=inputs)
            for parent_scope in self.scopes[-1]:
                new_scope.set_parent(parent_scope)
            self.scopes.append([new_scope])

    def pop_scope(self):
        if len(self.scopes) == 0:
            raise IndexError("No scopes to pop")
        self.scopes.pop()

    def push(self, ty: VType):
        if len(self.scopes) == 0:
            raise IndexError("No scopes to push to")
        for scope in self.scopes[-1]:
            scope.push(ty)

    def pop(self, n: int = 1):
        if len(self.scopes) == 0:
            raise IndexError("No scopes to pop from")
        for scope in self.scopes[-1]:
            scope.pop(n)

    def apply(self, overload_set: list[Overload]):
        if len(self.scopes) == 0:
            raise IndexError("No scopes to apply to")
        new_scopes: list[Scope] = []
        for scope in self.scopes[-1]:
            new_scopes.extend(scope.apply(overload_set))
        if not new_scopes:
            raise ValueError("No valid overloads found for application")
        self.scopes[-1] = new_scopes

    def get_element(self, ident: Identifier) -> list[Overload] | None:
        # None indicates that the element might need to be type-checked
        if ident in self.elements:
            return self.elements[ident]
        else:
            return None

    def add_element(self, ident: Identifier, overload: Overload):
        if ident not in self.elements:
            self.elements[ident] = []
        self.elements[ident].append(overload)

    def register_element(self, ident: Identifier, define_node: DefineNode):
        self.unchecked_elements[ident] = define_node

    def get_object(self, ident: Identifier) -> ObjectDef | None:
        # None indicates that the object might need to be type-checked
        if ident in self.objects:
            return self.objects[ident]
        else:
            return None

    def add_object(self, ident: Identifier, obj_def: ObjectDef):
        self.objects[ident] = obj_def

    def register_object(self, ident: Identifier, obj_def_node: ObjectDefinitionNode):
        self.unchecked_objects[ident] = obj_def_node

    def get_trait(self, ident: Identifier) -> TraitDef | None:
        # None indicates that the trait might need to be type-checked
        if ident in self.traits:
            return self.traits[ident]
        else:
            return None

    def add_trait(self, ident: Identifier, trait_def: TraitDef):
        self.traits[ident] = trait_def

    def register_trait(self, ident: Identifier, trait_impl_node: TraitNode):
        self.unchecked_traits[ident] = trait_impl_node

    def push_type_of(self, ast: ASTNode):
        if len(self.scopes) == 0:
            raise IndexError("No scopes to push to")
        for scope in self.scopes[-1]:
            scope.push(scope.type_of(ast))
