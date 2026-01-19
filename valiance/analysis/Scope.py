from valiance.compiler_common.Identifier import Identifier
from valiance.parser.AST import ASTNode
from valiance.vtypes.VTypes import InferenceTypeVariable, Overload, VType


class Scope:
    def __init__(self, inputs: list[VType] | None = None, parent: Scope | None = None):
        self.inputs = list(inputs) if inputs is not None else []
        self.stack: list[VType] = []
        self.variables: dict[Identifier, VType] = {}
        self.typemap: dict[InferenceTypeVariable, VType | None] = {}
        self.inference_variable_count = 0
        self.parent: Scope | None = parent

    def __repr__(self) -> str:
        stack_str = ", ".join(t.toString() for t in self.stack)
        return f"Scope(stack=[{stack_str}], variables={self.variables})"

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
        # Determine the list of scopes that could arise from applying an OverloadSet
        candidates = filter(lambda o: o.fits(self.stack), overload_set)
        scopes: list[Scope] = []
        for candidate in candidates:
            if len(self.stack) < candidate.arity:
                self.inputs.extend(
                    [
                        InferenceTypeVariable(self.inference_variable_count + i)
                        for i in range(candidate.arity - len(self.stack))
                    ]
                )
                self.inference_variable_count += candidate.arity - len(self.stack)
            new_scope = Scope(inputs=self.inputs.copy(), parent=self.parent)
            new_scope.stack = self.stack[::]
            new_scope.pop(candidate.arity)
            for ret in candidate.returns:
                new_scope.push(ret)
            scopes.append(new_scope)
        return scopes

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
