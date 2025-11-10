from typing import Callable, TypeVar
from valiance.lexer.Token import Token
from valiance.lexer.TokenType import TokenType
from valiance.parser.AST import (
    ASTNode,
    GroupNode,
    ListNode,
    LiteralNode,
    TupleNode,
    VariableSetNode,
)
from valiance.vtypes.VTypes import VType

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

    def head_equals(self, type_: TokenType) -> bool:
        if self.tokenStream:
            return self.tokenStream[0].type == type_
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
                    return LiteralNode(token.value, VType.NUMBER)
                case TokenType.STRING:
                    return LiteralNode(token.value, VType.STRING)
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
                if len(current_item) == 1:
                    elements.append(current_item[0])  # Single element
                else:
                    elements.append(GroupNode(current_item))
                current_item = []
                self.tokenStream.pop(0)  # Remove the comma
            else:
                element = self.parse_next()
                if element is not None:
                    current_item.append(element)
        if current_item:
            elements.append(GroupNode(current_item))
        self.tokenStream.pop(0)  # Remove the right square bracket
        return elements

    def parse_block(self) -> list[ASTNode]:
        elements: list[ASTNode] = []
        while self.tokenStream and self.tokenStream[0].type != TokenType.RIGHT_BRACE:
            element = self.parse_next()
            if element is not None:
                elements.append(element)
        self.tokenStream.pop(0)  # Remove the right brace
        return elements

    def parse_tuple(self) -> list[ASTNode]:
        elements: list[ASTNode] = []
        while self.tokenStream and self.tokenStream[0].type != TokenType.RIGHT_PAREN:
            element = self.parse_next()
            if element is not None:
                elements.append(element)
            if self.tokenStream and self.tokenStream[0].type == TokenType.COMMA:
                self.tokenStream.pop(0)  # Remove the comma
        self.tokenStream.pop(0)  # Remove the right parenthesis
        return elements
