from dataclasses import dataclass, field
from valiance.compiler_common.Identifier import Identifier
from valiance.analysis.Scope import ScopeStack
from valiance.analysis.StackState import StackState, MultiStack, SingleStack
from valiance.parser.AST import ASTNode, DefineNode, VariableSetNode
from vtypes.VTypes import FunctionType, Overload, VType


class Analyser:
    def __init__(self, ast: list[ASTNode], inference_needed: bool = False):
        self.ast = ast
        self.type_stack: StackState
        self.scope_stack = ScopeStack()
        if inference_needed:
            self.type_stack = MultiStack()
        else:
            self.type_stack = SingleStack()
        self.errors: list[AnalysisError] = []
        self.register_builtins()

    def analyse(self) -> "AnalysisResult":
        self._collect_declarations()
        self._check_all_definitions()
        self._check_top_level()
        return AnalysisResult(
            ast=self.ast,
            types={},  # Placeholder for type information
            scopes=self.scope_stack,
            errors=self.errors,
            success=len(self.errors) == 0,
        )

    def _collect_declarations(self):
        for node in self.ast:
            match node:
                case DefineNode():
                    name = node.name
                    inputs = node.inputs()
                    outputs = node.outputs()

                    if inputs is None or outputs is None:
                        self.scope_stack.add_definition(name, node)
                    else:
                        overload = Overload(inputs, outputs, len(inputs), len(outputs))
                        self.scope_stack.add_overload(name, overload)
                case VariableSetNode():
                    ...
                case _:
                    pass

    def _check_all_definitions(self):
        # Placeholder for checking all definitions
        pass

    def _check_top_level(self):
        # Placeholder for checking top-level code
        pass

    def register_builtins(self):
        import valiance.compiler_common.Primitives as Primitives

        for ident, overloads in Primitives.PRIMITIVES.items():
            for overload in overloads:
                self.scope_stack.add_overload(ident, overload)


@dataclass
class AnalysisResult:
    ast: list[ASTNode]
    types: dict[int, TypeInfo]  # id(node) → type info
    scopes: ScopeStack
    errors: list[AnalysisError]
    success: bool

    def get_type_of(self, node: ASTNode) -> TypeInfo | None:
        return self.types.get(id(node), None)


@dataclass
class TypeInfo:
    inferred_type: VType
    stack_before: list[VType]
    stack_after: list[VType]
    chosen_overload: Overload | None = None
    signature: FunctionType | None = None
    data_tags: set[Identifier] = field(default_factory=lambda: set())
    element_tags: set[Identifier] = field(default_factory=lambda: set())


@dataclass
class AnalysisError:
    message: str
    node: ASTNode
