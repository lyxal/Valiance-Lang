from typing import Callable, Tuple, TypeVar

import valiance.vtypes.VTypes as VTypes
from valiance.lexer.Token import Token
from valiance.lexer.TokenType import TokenType
from valiance.parser.AST import (
    ASTNode,
    AugmentedVariableSetNode,
    ElementNode,
    GroupNode,
    ListNode,
    LiteralNode,
    TupleNode,
    VariableGetNode,
    VariableSetNode,
)

T = TypeVar("T")


def unwrap_and_test(val: T | None, condition: Callable[[T], bool]) -> bool:
    """
    Unwrap an optional value and test it against a condition.

    :param val: The optional value to unwrap.
    :param condition: A callable that takes the unwrapped value and returns a bool.
    :return: True if the value is not None and the condition is met, False otherwise.
    """
    if val is not None:
        return condition(val)
    return False


class Parser:
    def __init__(self, tokenStream: list[Token]):
        self.tokenStream = tokenStream
        self.asts: list[ASTNode] = []

    def add_node(self, node: ASTNode):
        self.asts.append(node)

    def discard(self, count: int = 1):
        for _ in range(count):
            self.tokenStream.pop(0)

    def group_wrap(self, nodes: list[ASTNode]) -> ASTNode:
        if len(nodes) == 1:
            return nodes[0]
        return GroupNode(nodes)

    def head_equals(self, type_: TokenType) -> bool:
        if self.tokenStream:
            return self.tokenStream[0].type == type_
        return False

    def token_at_equals(self, index: int, type_: TokenType) -> bool:
        if len(self.tokenStream) > index:
            return self.tokenStream[index].type == type_
        return False

    def parse(self) -> list[ASTNode]:
        while self.tokenStream:
            node = self.parse_next()
            if node is not None:
                self.asts.append(node)
        return self.asts

    def peek(self) -> Token | None:
        if self.tokenStream:
            return self.tokenStream[0]
        return None

    def parse_next(self) -> ASTNode | None:
        while self.tokenStream:
            token = self.tokenStream.pop(0)
            match token.type:
                case TokenType.NUMBER:
                    return LiteralNode(token.value, VTypes.NumberType())
                case TokenType.STRING:
                    return LiteralNode(token.value, VTypes.StringType())
                case TokenType.LEFT_SQUARE:
                    # List literal
                    list_elements = self.parse_list()
                    return ListNode(list_elements)
                case TokenType.LEFT_BRACE:
                    # Block of code, just for grouping.
                    group_elements = self.parse_block()
                    return GroupNode(group_elements)
                case TokenType.LEFT_PAREN:
                    # A tuple. Won't conflict with `()` in function calls
                    # and function parameters, because those will consume
                    # parens as needed.
                    tuple_elements = self.parse_tuple()
                    return TupleNode(tuple_elements)
                case TokenType.VARIABLE:
                    if self.head_equals(TokenType.EQUALS):
                        # Variable assignment
                        self.discard()  # Discard the EQUALS token
                        value = self.parse_next()
                        if value is not None:
                            return VariableSetNode(token.value, value)
                        else:
                            raise Exception(
                                f"Expected value after '=' for variable '{token.value}' at line {token.line}, column {token.column}"
                            )
                    elif self.head_equals(TokenType.COLON):
                        # Augmented assignment
                        self.discard()  # Discard the COLON token
                        fn = self.parse_next()
                        if fn is not None:
                            return AugmentedVariableSetNode(token.value, fn)
                        else:
                            raise Exception(
                                f"Expected function after ':' for augmented variable '{token.value}' at line {token.line}, column {token.column}"
                            )
                    else:
                        return VariableGetNode(token.value)
                case TokenType.WORD:
                    # Element parsing
                    return self.parse_element(token)
                case TokenType.EOF:
                    break
                case _:
                    raise Exception(
                        f"Unexpected token {token.type} at line {token.line}, column {token.column}"
                    )
        return None

    def parse_list(self) -> list[ASTNode]:
        elements: list[ASTNode] = []
        current_item: list[ASTNode] = []
        while self.tokenStream and self.tokenStream[0].type != TokenType.RIGHT_SQUARE:
            if self.tokenStream[0].type == TokenType.COMMA:
                # End of current item
                elements.append(self.group_wrap(current_item))
                current_item = []
                self.tokenStream.pop(0)  # Remove the comma
            else:
                element = self.parse_next()
                if element is not None:
                    current_item.append(element)
        if current_item:
            elements.append(self.group_wrap(current_item))
        self.tokenStream.pop(0)  # Remove the right square bracket
        return elements

    def parse_block(self) -> list[ASTNode]:
        elements: list[ASTNode] = []
        while not self.head_equals(TokenType.RIGHT_BRACE):
            element = self.parse_next()
            if element is not None:
                elements.append(element)
        self.tokenStream.pop(0)  # Remove the right brace
        return elements

    def parse_tuple(self) -> list[ASTNode]:
        elements: list[ASTNode] = []
        current_item: list[ASTNode] = []
        while not self.head_equals(TokenType.RIGHT_PAREN):
            if self.head_equals(TokenType.COMMA):
                elements.append(self.group_wrap(current_item))
                current_item = []
                self.discard()  # Remove the comma
            element = self.parse_next()
            if element is not None:
                current_item.append(element)

        self.discard()  # Remove the right parenthesis
        return elements

    def parse_element(self, token: Token) -> ASTNode:
        element_name = token.value
        generics: list[VTypes.VType] = []
        element_call_args: list[Tuple[str, ASTNode]] = []
        modified: bool = False

        if self.head_equals(TokenType.LEFT_SQUARE):
            temp_generics: list[list[ASTNode]] = []
            current_generic: list[ASTNode] = []
            self.discard()  # Discard the LEFT_SQUARE
            while not self.head_equals(TokenType.RIGHT_SQUARE):
                type_ = self.parse_next()
                if type_ is not None:
                    current_generic.append(type_)
                if self.head_equals(TokenType.COMMA):
                    temp_generics.append(current_generic)
                    current_generic = []
                    self.discard()  # Discard the COMMA
            if current_generic:
                temp_generics.append(current_generic)
            generics += map(self.type_from_asts, temp_generics)
            self.discard()  # Discard the RIGHT_SQUARE

        if self.head_equals(TokenType.LEFT_PAREN):
            arguments: list[Tuple[str, ASTNode]] = []
            current_argument: list[ASTNode] = []
            current_argument_name: str = "_"
            self.discard()  # Discard the LEFT_PAREN
            while not self.head_equals(TokenType.RIGHT_PAREN):
                if self.head_equals(TokenType.COMMA):
                    self.discard()  # Discard the COMMA
                    if current_argument:
                        arg_node = self.group_wrap(current_argument)
                        arguments.append((current_argument_name, arg_node))
                        current_argument = []
                        current_argument_name = "_"
                if self.token_at_equals(1, TokenType.EQUALS):
                    if current_argument_name != "_":
                        raise Exception(
                            f"Unexpected equals sign in argument at line {token.line}, column {token.column}"
                        )
                    # Named argument
                    current_argument_name = self.tokenStream.pop(0).value
                    self.discard()  # Discard the EQUALS
                else:
                    value = self.parse_next()
                    if value is not None:
                        current_argument.append(value)
            if current_argument:
                arg_node = self.group_wrap(current_argument)
                arguments.append((current_argument_name, arg_node))
            element_call_args = arguments
            self.discard()  # Discard the RIGHT_PAREN

        if self.head_equals(TokenType.COLON):
            modified = True
            self.discard()  # Discard the MODIFIER

        return ElementNode(
            element_name=element_name,
            generics=generics,
            args=element_call_args,
            modified=modified,
        )

    def type_from_asts(self, asts: list[ASTNode]) -> VTypes.VType:
        return VTypes.CustomType("Todo: Implement")
