from valiance.compiler_common.Identifier import Identifier
from valiance.parser.AST import ASTNode
from valiance.vtypes.VTypes import InferenceTypeVariable, Overload, VType
from valiance.vtypes import VTypes


class Scope:
    def __init__(
        self,
        inputs: list[VType] | None = None,
        parent: Scope | None = None,
        allow_inference: bool = True,
    ):
        self.inputs = list(inputs) if inputs is not None else []
        self.stack: list[VType] = []
        self.variables: dict[Identifier, VType] = {}
        self.typemap: dict[InferenceTypeVariable, VType | None] = {}
        self.inference_variable_count = 0
        self.parent: Scope | None = parent
        self.allow_inference = allow_inference

    def __repr__(self) -> str:
        stack_str = ", ".join(t.toString() for t in self.stack)
        inputs_str = ", ".join(t.toString() for t in self.inputs)
        return f"Scope(inputs=[{inputs_str}], stack=[{stack_str}], variables={self.variables})"

    def push(self, ty: VType):
        self.stack.append(ty)

    def pop(self, n: int = 1):
        if n > len(self.stack):
            self.stack = []
        else:
            self.stack = self.stack[:-n]

    def set_variable(self, ident: Identifier):
        # Set a variable to the top of this scope's stack
        if len(self.stack) == 0:
            ty = InferenceTypeVariable(self.inference_variable_count)
            self.inference_variable_count += 1
            self.variables[ident] = ty
            self.typemap[ty] = None
        else:
            self.variables[ident] = self.stack.pop()

    def get_variable_type(self, ident: Identifier) -> VType | None:
        # Get the type of a variable in this scope
        if ident in self.variables:
            return self.variables[ident]
        elif self.parent is not None:
            # Try and find the variable in the parent scope
            return self.parent.get_variable_type(ident)
        else:
            return None

    def push_variable(self, ident: Identifier):
        # Push a variable from this scope onto the stack
        if ident in self.variables:
            self.stack.append(self.variables[ident])
        elif self.parent is not None:
            self.get_variable_type(ident)
        else:
            raise KeyError(f"Variable {ident.name} not found in scope")

    def apply(self, overload_set: list[Overload]) -> list[Scope]:
        if len(self.stack) > overload_set[0].arity or not self.allow_inference:
            return self.execute(overload_set)
        else:
            return self.infer(overload_set)

    def execute(self, overload_set: list[Overload]) -> list[Scope]:

        # Code to determine whether there is only one most specific overload
        # Can return [] if no overloads match
        candidates = list(filter(lambda o: o.fits(self.stack), overload_set))
        if not candidates:
            return []  # No matching overloads

        chosen = VTypes.choose_overload(candidates, self.stack)
        self.stack = self.stack[: -chosen.arity]
        self.stack.extend(chosen.returns)
        return [self]

    def infer(self, overload_set: list[Overload]) -> list[Scope]:
        # Code to create new scopes based on possible inferences
        # from the current stack and the overloads
        new_scopes: list[Scope] = []

        candidates = list(filter(lambda o: o.fits(self.stack), overload_set))
        for overload in candidates:
            # Create a new scope for each candidate overload
            # and pad inputs with the missing arguments from the overload.
            # Then push the return types onto the stack.
            new_scope = Scope(parent=self.parent, allow_inference=self.allow_inference)
            missing_args = overload.arity - len(self.stack)
            new_scope.inputs = (
                self.inputs + overload.params[-missing_args:]
                if missing_args > 0
                else self.inputs.copy()
            )
            new_scope.stack = self.stack.copy()
            new_scope.stack = new_scope.stack[: -overload.arity]
            new_scope.stack.extend(overload.returns)
            new_scopes.append(new_scope)

        return new_scopes

    def as_overload(self) -> Overload:
        return Overload(
            params=self.stack.copy(),
            returns=self.inputs.copy(),
            arity=len(self.stack),
            multiplicity=1,
        )

    def set_parent(self, parent: Scope):
        self.parent = parent

    def type_of(self, ast: ASTNode) -> VType:
        # Determine the type of an ASTNode relative to this scope
        match ast:
            case _:
                raise NotImplementedError(
                    f"Type determination for ASTNode of type {type(ast)} not implemented"
                )
