from typing import Callable, TypeVar, cast

from valiance.parser.Errors import GenericParseError
import valiance.vtypes.VTypes as VTypes

from valiance.parser.AST import *
from valiance.lexer.Token import Token
from valiance.lexer.TokenType import TokenType

T = TypeVar("T")
U = TypeVar("U")


def default_parse_items_wrap(x: list[T]) -> T:
    """
    A dummy wrap function that just returns the input as is.
    Useful for the default wrap parameter in parse_items.

    :param x: What would be wrapped
    :type x: list[T]
    :return: What the items would be wrapped into
    :rtype: T
    """
    return x


def is_element_token(token: Token) -> bool:
    """
    Test whether a token is a valid part of an element name.

    :param token: The token to test
    :type token: Token
    :return: True if the token is a valid element token, False otherwise
    :rtype: bool
    """
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


def testopt(val: T | None, condition: Callable[[T], bool]) -> bool:
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
        self.errors: list[GenericParseError] = []

    def add_node(self, node: ASTNode):
        """
        Add a node to the parser's AST list.

        :param self: This Parser instance
        :param node: The ASTNode to add
        :type node: ASTNode
        :return: None
        :rtype: None
        """
        self.asts.append(node)

    def discard(self, count: int = 1):
        """
        Discard a number of tokens from the head of the token stream.

        :param self: This Parser instance
        :param count: Number of tokens to discard
        :type count: int
        """
        for _ in range(count):
            self.tokenStream.pop(0)

    def group_wrap(self, nodes: list[ASTNode]) -> ASTNode:
        """
        Take a list of ASTNodes and return a single GroupNode if there are
        multiple nodes, or the single node itself if there's only one.

        :param self: This Parser instance
        :param nodes: List of ASTNodes to wrap
        :type nodes: list[ASTNode]
        :return: A single GroupNode if multiple nodes are provided, otherwise the single node itself
        :rtype: ASTNode
        """
        if len(nodes) == 1:
            return nodes[0]
        return GroupNode(nodes)

    def head_equals(self, type_: TokenType) -> bool:
        """
        Test whether the head token in the token stream matches the given type.

        :param self: This Parser instance
        :param type_: The TokenType to compare against the head token
        :type type_: TokenType
        :return: True if the head token matches the given type, False otherwise
        :rtype: bool
        """
        if self.tokenStream:
            return self.tokenStream[0].type == type_
        return False

    def head_is_any_of(self, types: list[TokenType]) -> bool:
        """
        Test whether the head token in the token stream matches any of the given types.

        :param self: This Parser instance
        :param types: List of TokenTypes to compare against the head token
        :type types: list[TokenType]
        :return: True if the head token matches any of the given types, False otherwise
        :rtype: bool
        """
        if self.tokenStream:
            return self.tokenStream[0].type in types
        return False

    def eat_whitespace(self):
        """
        Consume any leading whitespace tokens from the token stream.

        :param self: This Parser instance
        """
        while self.head_equals(TokenType.WHITESPACE):
            self.discard()

    def token_at_equals(self, index: int, type_: TokenType) -> bool:
        """
        Check whether the token at a specific index matches the given type.
        Returns False if the index is out of bounds.

        :param self: This Parser instance
        :param index: The index of the token to check
        :type index: int
        :param type_: The TokenType to compare against the token at the given index
        :type type_: TokenType
        :return: True if the token at the given index matches the given type, False otherwise
        :rtype: bool
        """
        if len(self.tokenStream) > index:
            return self.tokenStream[index].type == type_
        return False

    def parse(self) -> list[ASTNode]:
        """
        Parse this parser's list of tokens into AST nodes.

        :param self: This Parser instance
        :return: List of parsed AST nodes
        :rtype: list[ASTNode]
        """
        while self.tokenStream:
            node = self.parse_next()
            if node is not None:
                self.asts.append(node)
        return self.asts

    def peek(self) -> Token | None:
        """
        Peek at the head token in the token stream without consuming it.
        Returns None if the token stream is empty.

        :param self: This Parser instance
        :return: The head token if available, otherwise None
        :rtype: Token | None
        """
        if self.tokenStream:
            return self.tokenStream[0]
        return None

    def parse_items(
        self,
        close_token: TokenType,
        parse_fn: Callable[[], T | None],
        conglomerate: bool = False,  # Whether to wrap items in a GroupNode if multiple
        wrap_fn: Callable[
            [list[T]], T
        ] = default_parse_items_wrap,  # Function to wrap conglomerate items
        separator: TokenType = TokenType.COMMA,
        verify: Tuple[Callable[[list[T]], bool], str] | None = None,
    ) -> list[T]:
        """
        A generic-style item parser that can parse any number of separated items,
        stopping when a specified closing token is encountered.

        The parse_fn is used to determine how to parse each individual item.
        More often than not, this will be self.parse_next.

        Allows for conglomeration of items into a single wrapped item, especially useful
        for parsing things like lists or tuples, where multiple items need to be grouped together.

        The wrap_fn determines how to wrap conglomerate items. By default, it is a dummy function that
        just returns the list of items as is, useful for when conglomeration is not needed.

        More often than not, the wrap_fn will be self.group_wrap, which wraps multiple ASTNodes into a GroupNode.

        :param self: This Parser instance
        :param close_token: The token type that signifies the end of the item list
        :type close_token: TokenType
        :param parse_fn: The function to parse list items. Usually self.parse_next.
        :type parse_fn: Callable[[], T | None]
        :param conglomerate: Whether to wrap items using wrap_fn
        :type conglomerate: bool
        :param wrap_fn: Function to wrap conglomerate items.
        :type wrap_fn: Callable[[list[T]], T]
        :param separator: The token type that separates items in the list
        :type separator: TokenType
        :param verify: Optional function and error message to verify each parsed item. For example, a tuple may want to ensure items are expressionable.
        :type verify: (Callable[[list[T]], bool], str) | None
        :return: The list of parsed items, possibly wrapped if conglomerate is True
        :rtype: list[T]
        """
        items: list[T] = []  # The collected items
        current_item: list[T] = []  # Used to collect items before wrapping

        self.eat_whitespace()  # Consumption 1 - Pre-loop

        while not self.head_equals(close_token):
            self.eat_whitespace()  # Consumption 2 - Pre-separator

            if self.head_equals(separator):
                if conglomerate:
                    if not current_item:
                        raise Exception("Empty item detected.")
                    if verify is not None:
                        condition, error_msg = verify
                        if not condition(current_item):
                            raise GenericParseError(error_msg)
                    items.append(wrap_fn(current_item))
                else:
                    # If conglomerate is False, just extend the items list
                    items.extend(current_item)

                # Always reset current_item, regardless of conglomerate
                current_item = []

                self.discard()  # Remove the separator
                self.eat_whitespace()  # Consumption 3 - Post-separator

            item = parse_fn()  # Get the next item according to parse_fn
            if item is not None:
                current_item.append(item)
            self.eat_whitespace()  # Consumption 4 - Pre-close_token check in the next loop iteration

        # Make sure that any remaining items are added
        # This is necessary because the last item won't be followed by a separator
        # Make sure to wrap if conglomerate is True
        if conglomerate and current_item:
            items.append(wrap_fn(current_item))
        elif not conglomerate:
            items.extend(current_item)

        # Finally, eat any trailing whitespace before the closing token
        self.eat_whitespace()
        self.discard()  # Discard the closing token
        return items

    def quick_items(
        self,
        close_token: TokenType,
        verify: Tuple[Callable[[list[ASTNode]], bool], str] | None = None,
    ) -> list[ASTNode]:
        """
        A simplified version of parse_items that specifically parses ASTNodes
        until a specified closing token is encountered.

        This method uses self.parse_next as the parsing function, conglomerates,
        and wraps items using self.group_wrap.

        Very useful for parsing lists, tuples, and similar structures where
        you don't care about specialising.

        :param self: This Parser instance
        :param close_token: The token type that signifies the end of the item list
        :type close_token: TokenType
        :return: The list of parsed ASTNodes
        :rtype: list[ASTNode]
        """
        return self.parse_items(
            close_token,
            self.parse_next,
            conglomerate=True,
            wrap_fn=self.group_wrap,
            separator=TokenType.COMMA,
            verify=verify,
        )

    def parse_next(self) -> ASTNode | None:
        """
        Parse and return the next AST node from the token stream.

        :param self: This Parser instance
        :return: The next parsed AST node if available, otherwise None
        :rtype: ASTNode | None
        """
        self.eat_whitespace()
        token = self.tokenStream.pop(0)
        match token.type:
            case TokenType.NUMBER:
                return LiteralNode(token.value, VTypes.NumberType())
            case TokenType.STRING:
                return LiteralNode(token.value, VTypes.StringType())
            case TokenType.LEFT_PAREN:
                return self.parse_tuple()
            case TokenType.LEFT_SQUARE:
                return self.parse_list_or_dictionary()
            case TokenType.LEFT_BRACE:
                return self.parse_block()
            case TokenType.VARIABLE:
                return self.parse_variable(variable_token=token)
            case TokenType.MULTI_VARIABLE:
                return self.parse_multi_variable()
            case _ if token.type == TokenType.WORD or is_element_token(token):
                return self.parse_element(initial_token=token)
            case TokenType.DUPLICATE:
                return self.parse_labelled(ast_type=DuplicateNode)
            case TokenType.SWAP:
                return self.parse_labelled(ast_type=SwapNode)
            case TokenType.UNDERSCORE:
                return self.parse_labelled(ast_type=PopNode)
            case TokenType.FN:
                return self.parse_function()
            case TokenType.SINGLE_QUOTE:
                return self.parse_quick_function()
            case TokenType.TILDE:
                return self.parse_index_dump()
            case TokenType.AS:
                return self.parse_type_cast(safe=True)
            case TokenType.AS_UNSAFE:
                return self.parse_type_cast(safe=False)
            case TokenType.MATCH:
                return self.parse_match_expr()
            case TokenType.IF:
                return self.parse_if_expr()
            case TokenType.FOREACH:
                return self.parse_foreach_expr()
            case TokenType.WHILE:
                return self.parse_while_expr()
            case TokenType.UNFOLD:
                return self.parse_unfold_expr()
            case TokenType.DEFINE:
                return self.parse_define()
            case TokenType.OBJECT:
                return self.parse_object()
            case TokenType.TRAIT:
                return self.parse_trait()
            case TokenType.VARIANT:
                return self.parse_variant()
            case TokenType.ENUM:
                return self.parse_enum()
            case TokenType.TAG:
                return self.parse_tag()
            case TokenType.ANNOTATION:
                return self.parse_annotation()
            case TokenType.TRY:
                return self.parse_try_handle()
            case TokenType.PANIC_KEYWORD:
                return self.parse_panic()
            case TokenType.SPAWN:
                return self.parse_spawn()
            case TokenType.CONCURRENT:
                return self.parse_concurrent()
            case TokenType.AT:
                return self.parse_at()
            case TokenType.ASSERT:
                return self.parse_assert()
            case TokenType.IMPORT:
                return self.parse_import()
            case _:
                return None

    # Specialised parse methods start here

    def parse_tuple(self) -> ASTNode:
        tuple_items = self.quick_items(
            TokenType.RIGHT_PAREN,
            verify=(self.is_expressionable, "Tuple items must be expressionable."),
        )
        return TupleNode(tuple_items, len(tuple_items))

    def parse_list_or_dictionary(self) -> ASTNode:
        items = self.quick_items(TokenType.RIGHT_SQUARE)

        # See if any items were collected
        if not items:
            return ListNode([])  # This _will_ need to be disambiguated by the user

        # Now determine if this is a dictionary or a list
        return NotImplementedError

    def parse_block(self) -> ASTNode:
        return NotImplementedError

    def parse_variable(self, variable_token: Token) -> ASTNode:
        return NotImplementedError

    def parse_multi_variable(self) -> ASTNode:
        return NotImplementedError

    def parse_element(self, initial_token: Token) -> ASTNode:
        return NotImplementedError

    def parse_labelled(self, ast_type: type[ASTNode]) -> ASTNode:
        return NotImplementedError

    def parse_function(self) -> ASTNode:
        return NotImplementedError

    def parse_quick_function(self) -> ASTNode:
        return NotImplementedError

    def parse_index_dump(self) -> ASTNode:
        return NotImplementedError

    def parse_type_cast(self, safe: bool) -> ASTNode:
        return NotImplementedError

    def parse_match_expr(self) -> ASTNode:
        return NotImplementedError

    def parse_if_expr(self) -> ASTNode:
        return NotImplementedError

    def parse_foreach_expr(self) -> ASTNode:
        return NotImplementedError

    def parse_while_expr(self) -> ASTNode:
        return NotImplementedError

    def parse_unfold_expr(self) -> ASTNode:
        return NotImplementedError

    def parse_define(self) -> ASTNode:
        return NotImplementedError

    def parse_object(self) -> ASTNode:
        return NotImplementedError

    def parse_trait(self) -> ASTNode:
        return NotImplementedError

    def parse_variant(self) -> ASTNode:
        return NotImplementedError

    def parse_enum(self) -> ASTNode:
        return NotImplementedError

    def parse_tag(self) -> ASTNode:
        return NotImplementedError

    def parse_annotation(self) -> ASTNode:
        return NotImplementedError

    def parse_try_handle(self) -> ASTNode:
        return NotImplementedError

    def parse_panic(self) -> ASTNode:
        return NotImplementedError

    def parse_spawn(self) -> ASTNode:
        return NotImplementedError

    def parse_concurrent(self) -> ASTNode:
        return NotImplementedError

    def parse_at(self) -> ASTNode:
        return NotImplementedError

    def parse_assert(self) -> ASTNode:
        return NotImplementedError

    def parse_import(self) -> ASTNode:
        return NotImplementedError

    # Parsing helper methods
    def is_expressionable(self, nodes: list[ASTNode]) -> bool:
        """
        Check whether all ASTNodes in the provided list are expressionable.

        :param self: This Parser instance
        :param nodes: List of ASTNodes to check
        :type nodes: list[ASTNode]
        :return: True if all nodes are expressionable, False otherwise
        :rtype: bool
        """

        # Check if each node is an instance of a node that is expressionable
        for node in nodes:
            if isinstance(node, GroupNode):
                for child in node.elements:
                    if not self.is_expressionable([child]):
                        return False
            if not isinstance(
                node,
                (
                    LiteralNode,
                    ElementNode,
                    FunctionNode,
                    ListNode,
                    TupleNode,
                    DictionaryNode,
                    VariableGetNode,
                    DuplicateNode,
                    SwapNode,
                    PopNode,
                    IfNode,
                    MatchNode,
                    WhileNode,
                    ForNode,
                    UnfoldNode,
                    AssertNode,
                    AssertElseNode,
                    TypeCastNode,
                ),
            ):
                return False
        return True
