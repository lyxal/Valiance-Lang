import itertools
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


def is_element_token(token: Token) -> bool:
    return token.type in (
        TokenType.WORD,
        TokenType.MINUS,
        TokenType.PLUS,
        TokenType.AMPERSAND,
        TokenType.STAR,
        TokenType.SLASH,
        TokenType.PERCENT,
        TokenType.EXCLAMATION,
        TokenType.LESS_THAN,
        TokenType.GREATER_THAN,
        TokenType.QUESTION,
        TokenType.UNDERSCORE,
    )


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

    def head_is_any_of(self, types: list[TokenType]) -> bool:
        if self.tokenStream:
            return self.tokenStream[0].type in types
        return False

    def numch_whitespace(self):
        # Consume whitespace tokens at the head of the token stream
        while self.head_equals(TokenType.WHITESPACE):
            self.discard()

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
                case TokenType.WHITESPACE:
                    continue
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
                    if self.head_equals(TokenType.EQUALS) and not self.token_at_equals(
                        1, TokenType.EQUALS
                    ):
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
                case _ if token.type == TokenType.WORD or is_element_token(token):
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
        while not self.head_equals(TokenType.RIGHT_SQUARE):
            self.numch_whitespace()
            if self.head_equals(TokenType.COMMA):
                if not current_item:
                    raise Exception("Empty list item detected.")
                elements.append(self.group_wrap(current_item))
                current_item = []
                self.discard()  # Remove the comma
            element = self.parse_next()
            if element is not None:
                current_item.append(element)

        if current_item:
            elements.append(self.group_wrap(current_item))

        self.discard()  # Remove the right bracket
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
            self.numch_whitespace()
            if self.head_equals(TokenType.COMMA):
                if not current_item:
                    raise Exception("Empty tuple item detected.")
                elements.append(self.group_wrap(current_item))
                current_item = []
                self.discard()  # Remove the comma
            element = self.parse_next()
            if element is not None:
                current_item.append(element)

        if current_item:
            elements.append(self.group_wrap(current_item))

        self.discard()  # Remove the right parenthesis
        return elements

    def parse_element(self, first_token: Token) -> ASTNode:
        element_name = first_token.value

        while self.tokenStream and (
            is_element_token(self.tokenStream[0])
            or self.tokenStream[0].type == TokenType.NUMBER
        ):
            element_name += self.tokenStream.pop(0).value

        generics: list[VTypes.VType] = []
        arguments: list[Tuple[str, ASTNode]] = []

        if self.head_equals(TokenType.LEFT_SQUARE):
            generics = self.parse_type_parameters()

        if self.head_equals(TokenType.LEFT_PAREN):
            arguments = self.parse_element_arguments()

        modified = False
        self.numch_whitespace()
        if self.head_equals(TokenType.COLON):
            modified = True
            self.discard()  # Remove the modifier token

        return ElementNode(element_name, generics, arguments, modified)

    def parse_type_parameters(self) -> list[VTypes.VType]:
        generics: list[VTypes.VType] = []
        self.discard()  # Discard the LEFT_SQUARE

        while not self.head_equals(TokenType.RIGHT_SQUARE):
            self.numch_whitespace()
            generics.append(self.parse_type())
            self.numch_whitespace()
            if self.head_equals(TokenType.COMMA):
                self.discard()  # Discard the COMMA
            elif not self.head_equals(TokenType.RIGHT_SQUARE):
                raise Exception("Expected comma in generic parameters but found none.")
            else:
                break

        self.discard()  # Discard the RIGHT_SQUARE
        return generics

    def parse_type(self) -> VTypes.VType:
        lhs = self.parse_union_type()
        self.numch_whitespace()
        if self.head_equals(TokenType.AMPERSAND):
            self.discard()  # Discard the AMPERSAND
            self.numch_whitespace()
            rhs = self.parse_union_type()
            return VTypes.IntersectionType(lhs, rhs)
        return lhs

    def parse_union_type(self) -> VTypes.VType:
        lhs = self.parse_primary_type()
        self.numch_whitespace()
        if self.head_equals(TokenType.PIPE):
            self.discard()  # Discard the PIPE
            self.numch_whitespace()
            rhs = self.parse_primary_type()
            return VTypes.UnionType(lhs, rhs)
        return lhs

    def parse_primary_type(self) -> VTypes.VType:
        # First, the base type
        base_type: VTypes.VType = VTypes.VType()
        if self.head_equals(TokenType.WORD):
            type_token = self.tokenStream.pop(0)
            match type_token.value:
                case "Number":
                    base_type = VTypes.NumberType()
                case "String":
                    base_type = VTypes.StringType()
                case "Dictionary":
                    if not self.head_equals(TokenType.LEFT_SQUARE):
                        raise Exception(
                            "Expected '[' after 'Dictionary' in type declaration."
                        )
                    self.discard()  # Discard LEFT_SQUARE
                    self.numch_whitespace()
                    key_type = self.parse_type()
                    self.numch_whitespace()
                    if not self.head_equals(TokenType.ARROW):
                        raise Exception("Expected '->' in Dictionary type declaration.")
                    self.discard()  # Discard the ARROW
                    self.numch_whitespace()
                    value_type = self.parse_type()
                    base_type = VTypes.DictionaryType(key_type, value_type)
                    self.numch_whitespace()
                    if not self.head_equals(TokenType.RIGHT_SQUARE):
                        raise Exception(
                            "Expected ']' at the end of Dictionary type declaration."
                        )
                    self.discard()  # Discard RIGHT_SQUARE
                case "Function":
                    base_type = self.parse_function_type(function_token_skipped=True)
                    pass
                case _:
                    type_parameters: list[VTypes.VType] = []
                    if self.head_equals(TokenType.LEFT_SQUARE):
                        type_parameters = self.parse_type_parameters()
                    base_type = VTypes.CustomType(type_token.value, type_parameters)
        elif self.head_equals(TokenType.LEFT_PAREN):
            self.discard()  # Discard LEFT_PAREN
            element_types: list[VTypes.VType] = []
            while not self.head_equals(TokenType.RIGHT_PAREN):
                self.numch_whitespace()
                element_types.append(self.parse_type())
                if self.head_equals(TokenType.COMMA):
                    self.discard()  # Discard COMMA
            self.discard()  # Discard RIGHT_PAREN
            base_type = VTypes.TupleType(element_types)
        else:
            raise Exception("Expected type but found none.")

        # Now, the type modifiers
        modifiers: list[TokenType] = []
        while self.head_is_any_of([TokenType.PLUS, TokenType.STAR, TokenType.TILDE]):
            modifiers.append(self.tokenStream.pop(0).type)

        grouped_modifiers = itertools.groupby(modifiers)
        for modifier, group in grouped_modifiers:
            count = len(list(group))
            match modifier:
                case TokenType.PLUS:
                    base_type = VTypes.ExactRankType(base_type, count)
                case TokenType.STAR:
                    base_type = VTypes.MinimumRankType(base_type, count)
                case TokenType.TILDE:
                    base_type = VTypes.ListType(base_type, count)
                case _:
                    pass  # Will not happen

        while self.head_equals(TokenType.QUESTION):
            self.discard()  # Discard QUESTION
            base_type = VTypes.OptionalType(base_type)

        return base_type

    def parse_function_type(self, function_token_skipped: bool = False) -> VTypes.VType:
        if not function_token_skipped:
            self.discard()  # Discard FUNCTION token
        self.numch_whitespace()
        if not self.head_equals(TokenType.LEFT_SQUARE):
            raise Exception("Expected '[' at the start of function type parameters.")

        param_types: list[VTypes.VType] = []
        self.discard()  # Discard LEFT_SQUARE
        self.numch_whitespace()

        if self.head_equals(TokenType.RIGHT_SQUARE):
            # No parameters
            self.discard()  # Discard RIGHT_SQUARE
            self.numch_whitespace()
            return VTypes.FunctionType(False, [], [], [], [])

        while not self.head_equals(TokenType.ARROW):
            param_types.append(self.parse_type())
            self.numch_whitespace()
            if self.head_equals(TokenType.COMMA):
                self.discard()  # Discard COMMA
                self.numch_whitespace()
            elif not self.head_equals(TokenType.ARROW):
                raise Exception(
                    "Expected comma or '->' in function type input parameters."
                )
            else:
                break
        self.discard()  # Discard ARROW
        self.numch_whitespace()
        return_types: list[VTypes.VType] = []
        while not self.head_equals(TokenType.RIGHT_SQUARE):
            return_types.append(self.parse_type())
            self.numch_whitespace()
            if self.head_equals(TokenType.COMMA):
                self.discard()  # Discard COMMA
                self.numch_whitespace()
            elif not self.head_equals(TokenType.RIGHT_SQUARE):
                raise Exception("Expected comma or ']' in function type return types.")
            else:
                break
        self.discard()  # Discard RIGHT_SQUARE
        # TODO: Where clauses
        return VTypes.FunctionType(True, [], param_types, return_types, [])

    def parse_element_arguments(self) -> list[Tuple[str, ASTNode]]:
        arguments: list[Tuple[str, ASTNode]] = []
        self.discard()  # Discard LEFT_PAREN

        while not self.head_equals(TokenType.RIGHT_PAREN):
            self.numch_whitespace()
            arg_name = ""
            elements: list[ASTNode] = []
            if self.head_equals(TokenType.WORD):
                temp_token = self.tokenStream.pop(0)
                self.numch_whitespace()
                if self.head_equals(TokenType.EQUALS):
                    arg_name_token = temp_token
                    arg_name = arg_name_token.value
                    self.discard()  # Discard EQUALS
                else:
                    elements.append(
                        self.parse_element(temp_token)
                    )  # The word was part of the element
            while not self.head_equals(TokenType.COMMA) and not self.head_equals(
                TokenType.RIGHT_PAREN
            ):
                element = self.parse_next()
                if element is not None:
                    elements.append(element)
            arguments.append((arg_name, self.group_wrap(elements)))
            if self.head_equals(TokenType.COMMA):
                self.discard()  # Discard COMMA
            elif not self.head_equals(TokenType.RIGHT_PAREN):
                raise Exception(
                    "Expected comma or right parenthesis in element arguments."
                )
            else:
                break
        self.discard()  # Discard RIGHT_PAREN
        return arguments
