from valiance.analyser.Symbol import Symbol
from valiance.compiler_common.Identifier import Identifier
from valiance.analyser.TypedAST import TypedAST
import valiance.parser.AST as AST
from valiance.analyser.Symbol import *


class Analyser:
    def __init__(self, nodes: list[AST.ASTNode]):
        self.nodes = nodes
        self.tnodes: list[TypedAST] = []
        self.symbols: dict[Identifier, Symbol] = {}

    def analyse(self) -> list[TypedAST]:
        self.symbols = self.collect_names()
        return self.tnodes

    def collect_names(self) -> dict[Identifier, Symbol]:
        for node in self.nodes:
            match node:
                case AST.DefineNode(
                    name=name,
                    generics=generics,
                    parameters=parameters,
                    element_tags=element_tags,
                    output=output,
                ):
                    self.symbols[name] = DefineSymbol(
                        generics=generics,
                        parameters=[param.type_ for param in parameters],
                        element_tags=element_tags,
                        outputs=output,
                    )
                case AST.ObjectDefinitionNode(
                    object_name=name, fields=fields, generics=generics
                ):
                    self.symbols[name] = ObjectSymbol(
                        fields=fields,
                        generics=generics,
                    )
                case AST.VariableSetNode(name=name):
                    self.symbols[name] = VariableSymbol(type_=None)
                case _:  # A node that isn't actually a symbol.
                    continue
        return self.symbols
