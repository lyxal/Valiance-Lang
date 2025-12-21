import enum
import itertools
from typing import Callable, TypeVar, cast, overload

from valiance.compiler_common import ReservedWords
from valiance.parser.Errors import GenericParseError
import valiance.vtypes.VTypes as VTypes

from valiance.parser.AST import *
from valiance.lexer.Token import Token
from valiance.lexer.TokenType import TokenType

T = TypeVar("T")
U = TypeVar("U")

TYPE_OPERATOR_PRECEDENCE_SET = [{"|"}, {"&"}]
TYPE_OPERATOR_PRECEDENCE_TABLE: dict[str, int] = {}
for precedence, operators in enumerate(TYPE_OPERATOR_PRECEDENCE_SET):
    for operator in operators:
        TYPE_OPERATOR_PRECEDENCE_TABLE[operator] = precedence


class DictCheckReturnValue(enum.Enum):
    YES = enum.auto()
    NO = enum.auto()
    ERROR = enum.auto()


def default_parse_items_wrap(x: list[T]) -> T:
    """
    A dummy wrap function that just returns the input as is.
    Useful for the default wrap parameter in parse_items.

    :param x: What would be wrapped
    :type x: list[T]
    :return: What the items would be wrapped into
    :rtype: T
    """
    return x  # type: ignore


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


def location_from_token(token: Token) -> Location:
    """
    Create a Location object from a Token's location information.

    :param token: The token to extract location from
    :type token: Token
    :return: A Location object representing the token's location
    :rtype: Location
    """
    return Location(token.line, token.column)


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

    def add_error(
        self, message: str, location: Location, class_: type = GenericParseError
    ):
        """
        Add a parsing error to the parser's error list.

        :param self: This Parser instance
        :param message: The error message
        :type message: str
        :param location: The (line, column) location of the error
        :type location: (int, int)
        :param class_: The class of the error to create
        :type class_: type
        """
        error = class_(message, location)
        self.errors.append(error)

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

    def eat(self, type_: TokenType) -> Token | None:
        """
        Consume and return the head token if it matches the given type.
        Returns None if the head token does not match.

        :param self: This Parser instance
        :param type_: The TokenType to match against the head token
        :type type_: TokenType
        :return: The head token if it matches the given type, otherwise None
        :rtype: Token | None
        """
        if self.head_equals(type_):
            return self.pop()
        self.add_error(
            "Expected token of type "
            + str(type_)
            + " but found "
            + str(self.head().type),
            location_from_token(self.head()),
        )
        return None

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
        return GroupNode(nodes[0].location if nodes else Location(0, 0), nodes)

    def head(self) -> Token:
        """
        Get the head token in the token stream. Only use if you are sure
        there is at least one token available.

        :param self: This Parser instance
        :return: The head token
        :rtype: Token
        """
        return self.tokenStream[0]

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

    def head_lookahead_equals(self, types: list[TokenType]) -> bool:
        """
        Test whether the first few tokens in the token stream match the given types.

        :param self: This Parser instance
        :param types: The list of TokenTypes to compare against the head tokens
        :type types: list[TokenType]
        :return: True if the head tokens match the given types, False otherwise
        :rtype: bool
        """

        # A simple for-loop does not account for extra whitespace within
        # the token stream, so a manual count is needed
        check_index = 0
        stream_length = len(self.tokenStream)

        while check_index < stream_length:
            # Skip whitespace tokens
            if self.tokenStream[check_index].type == TokenType.WHITESPACE:
                check_index += 1
                continue

            # If we've run out of types to check against, return True
            if len(types) == 0:
                return True

            # Compare the current token with the first type in the list
            if self.tokenStream[check_index].type != types[0]:
                return False

            # Move to the next type and token
            types.pop(0)
            check_index += 1

        # If there are still types left to check, return False
        return len(types) == 0

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

    def parse(self) -> list[ASTNode] | list[GenericParseError]:
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
        if self.errors:
            return self.errors
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

    def pop(self) -> Token:
        """
        Pop and return the head token from the token stream.
        Raises an exception if the token stream is empty.

        :param self: This Parser instance
        :return: The head token
        :rtype: Token
        """
        if not self.tokenStream:
            raise Exception("Attempted to pop from an empty token stream.")
        return self.tokenStream.pop(0)

    def parse_items(
        self,
        close_token: TokenType | list[TokenType],
        parse_fn: Callable[[], T | None],
        conglomerate: bool = False,  # Whether to wrap items in a GroupNode if multiple
        wrap_fn: Callable[
            [list[T]], T
        ] = default_parse_items_wrap,  # Function to wrap conglomerate items
        separator: TokenType = TokenType.COMMA,
        verify: (
            Tuple[Callable[[list[T]], bool], str, Callable[[list[T]], Location]] | None
        ) = None,
        yeet_closer: bool = True,
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
        :param yeet_closer: Discard the closing token if true
        :type yeet_closer: bool
        :return: The list of parsed items, possibly wrapped if conglomerate is True
        :rtype: list[T]
        """
        items: list[T] = []  # The collected items
        current_item: list[T] = []  # Used to collect items before wrapping

        if isinstance(close_token, TokenType):
            close_token = [close_token]

        self.eat_whitespace()  # Consumption 1 - Pre-loop

        while self.tokenStream and not self.head_is_any_of(close_token):
            self.eat_whitespace()  # Consumption 2 - Pre-separator

            if self.head_equals(separator):
                if conglomerate:
                    if not current_item:
                        raise Exception("Empty item detected.")
                    if verify is not None:
                        condition, error_msg, get_location = verify
                        if not condition(current_item):
                            self.add_error(
                                error_msg,
                                get_location(current_item),
                            )
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

        # At this point, we should be at the close_token
        # So verify that the token is indeed the close_token
        if not self.head_is_any_of(close_token):
            token_names = ", ".join(token.name for token in close_token)
            if not self.peek():
                self.add_error(
                    f"Expected closing token {token_names} but reached end of file.",
                    Location(0, 0),
                )
            else:
                self.add_error(
                    f"Expected closing token {token_names} not found.",
                    Location(
                        self.peek().line if self.peek() else 0,  # type: ignore
                        self.peek().column if self.peek() else 0,  # type: ignore
                    ),
                )
            return []

        # Make sure that any remaining items are added
        # This is necessary because the last item won't be followed by a separator
        # Make sure to wrap if conglomerate is True
        if conglomerate and current_item:
            items.append(wrap_fn(current_item))
        elif not conglomerate:
            items.extend(current_item)

        # Finally, eat any trailing whitespace before the closing token
        self.eat_whitespace()
        if yeet_closer:
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
        location_fn: Callable[[list[ASTNode]], Location] = lambda nodes: (
            nodes[0].location if nodes else Location(0, 0)
        )
        location_fn = lambda nodes: nodes[0].location if nodes else Location(0, 0)
        return self.parse_items(
            close_token,
            self.parse_next,
            conglomerate=True,
            wrap_fn=self.group_wrap,
            separator=TokenType.COMMA,
            verify=(verify[0], verify[1], location_fn) if verify else None,
        )

    def collect_until(self, stop_tokens: list[TokenType]) -> list[ASTNode]:
        """
        An even more simplified version of parse_items that collects ASTNodes
        until one of the specified stop tokens is encountered. No separators
        involved. Always keeps the stop token.

        :param self: This Parser instance
        :param stop_tokens: The token types that signify the end of the collection
        :type stop_tokens: list[TokenType]
        :return: The list of collected ASTNodes
        :rtype: list[ASTNode]
        """

        items: list[ASTNode] = []
        self.eat_whitespace()
        while self.tokenStream and not self.head_is_any_of(stop_tokens):
            node = self.parse_next()
            if node is not None:
                items.append(node)
            self.eat_whitespace()
        return items

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
                return LiteralNode(
                    location_from_token(token), token.value, VTypes.NumberType()
                )
            case TokenType.STRING:
                return LiteralNode(
                    location_from_token(token), token.value, VTypes.StringType()
                )
            case TokenType.LEFT_PAREN:
                return self.parse_tuple(token)
            case TokenType.LEFT_SQUARE:
                return self.parse_list_or_dictionary(token)
            case TokenType.LEFT_BRACE:
                return self.parse_block()
            case TokenType.VARIABLE:
                return self.parse_variable(variable_token=token)
            case TokenType.MULTI_VARIABLE:
                return self.parse_multi_variable(variable_token=token)
            case _ if token.type == TokenType.WORD or is_element_token(token):
                return self.parse_element(initial_token=token)
            case TokenType.DUPLICATE:
                return self.parse_labelled(ast_type=DuplicateNode, token=token)
            case TokenType.SWAP:
                return self.parse_labelled(ast_type=SwapNode, token=token)
            case TokenType.UNDERSCORE:
                return self.parse_labelled(ast_type=PopNode, token=token)
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

    def parse_tuple(self, head_token: Token) -> ASTNode:
        tuple_items = self.quick_items(
            TokenType.RIGHT_PAREN,
            verify=(self.is_expressionable, "Tuple items must be expressionable."),
        )
        return TupleNode(location_from_token(head_token), tuple_items, len(tuple_items))

    def parse_list_or_dictionary(self, head_token: Token) -> ASTNode | None:
        """
        Parse either a list or a dictionary from the token stream,
        depending on the structure of the items found within the brackets.

        :param self: This Parser instance
        :param head_token: The opening LEFT_SQUARE token
        :return: A ListNode or DictionaryNode depending on the parsed structure, or None on error
        :rtype: ASTNode | None
        """

        # Manually collect items because we need to disambiguate
        # between lists and dictionaries
        items = self.parse_items(
            TokenType.RIGHT_SQUARE,
            self.parse_list_item,
            conglomerate=True,
            separator=TokenType.COMMA,
            wrap_fn=self.group_wrap,
        )

        # See if any items were collected
        if not items:
            return ListNode(
                location_from_token(head_token), []
            )  # This _will_ need to be disambiguated by the user

        # Get the collection type of the first item
        dict_check = self.is_dictionary_item(items[0])
        # If there's more than 1 item, ensure subsequent items are
        # the same
        if len(items) > 1:
            for item in items[1:]:
                next_check = self.is_dictionary_item(item)
                if next_check.name != dict_check.name:
                    if dict_check == DictCheckReturnValue.YES:
                        self.add_error(
                            "Non-dictionary item found in dictionary.",
                            item.location,
                        )
                    else:
                        self.add_error(
                            "Dictionary item found in list.",
                            item.location,
                        )
                    dict_check = DictCheckReturnValue.ERROR
                    return None

        # At this point, we know whether it's a list or dictionary
        if dict_check == DictCheckReturnValue.YES:
            # It's a dictionary
            dict_entries: list[Tuple[ASTNode, ASTNode]] = []
            for item in items:
                assert isinstance(item, GroupNode)
                dict_entries.append(self.extract_dict_items(item))
            return DictionaryNode(location_from_token(head_token), dict_entries)
        elif dict_check == DictCheckReturnValue.NO:
            # It's a list
            list_items: list[ASTNode] = []
            for item in items:
                if isinstance(item, GroupNode):
                    list_items.extend(item.elements)
                else:
                    list_items.append(item)
            return ListNode(location_from_token(head_token), list_items)
        else:
            return None

    def parse_block(self) -> ASTNode:
        return self.group_wrap(
            self.parse_items(
                TokenType.RIGHT_BRACE,
                self.parse_next,
                conglomerate=True,
                separator=TokenType.DUMMY_TOKEN_TYPE,
                wrap_fn=self.group_wrap,
            )
        )

    def parse_variable(self, variable_token: Token) -> ASTNode | None:
        self.eat_whitespace()
        if not self.peek() or (self.peek() and self.peek().type != TokenType.EQUALS):  # type: ignore
            # A simple variable get
            return VariableGetNode(
                location_from_token(variable_token), variable_token.value
            )

        # A variable set
        self.discard()  # Discard the EQUALS token
        value: list[ASTNode] = []
        while self.tokenStream and not self.head_equals(TokenType.NEWLINE):
            self.eat_whitespace()
            node = self.parse_next()
            if node is not None:
                if not self.is_expressionable([node]):
                    self.add_error(
                        "Variable assignment value must be expressionable.",
                        node.location,
                    )
                    return None
                else:
                    value.append(node)
        return VariableSetNode(
            location_from_token(variable_token),
            variable_token.value,
            self.group_wrap(value),
        )

    def parse_multi_variable(self, variable_token: Token) -> ASTNode | None:
        self.eat_whitespace()
        variable_names: list[str] = []
        errored: bool = False
        while self.tokenStream and not self.head_equals(TokenType.RIGHT_PAREN):
            if (
                self.head_equals(TokenType.WORD)
                or self.head().value in ReservedWords.RESERVED_WORDS
            ):
                variable_names.append(self.head().value)
            else:
                self.add_error(
                    f"Expected variable name in multi-variable declaration. Got '{self.head().value}'.",
                    location_from_token(self.head()) if self.peek() else Location(0, 0),
                )
                errored = True

            # Discard even after error to sync up to a closing parenthesis
            # if that's even present.
            self.discard()
            self.eat_whitespace()

            if self.head_equals(TokenType.COMMA):
                self.discard()
                self.eat_whitespace()
            elif self.head_equals(TokenType.RIGHT_PAREN):
                break
            else:
                self.add_error(
                    "Expected ',' between variable names in multi-variable declaration.",
                    location_from_token(self.head()) if self.peek() else Location(0, 0),
                )
                self.discard()
        self.eat_whitespace()
        if not self.head_equals(TokenType.RIGHT_PAREN):
            self.add_error(
                "Expected ')' after multi-variable declaration.",
                location_from_token(self.head()) if self.peek() else Location(0, 0),
            )
            return None
        if errored:  # Don't try to continue if there were errors
            return None
        self.discard()  # Discard the RIGHT_PAREN token
        self.eat_whitespace()
        if not self.head_equals(TokenType.EQUALS):
            self.add_error(
                "Expected '=' after multi-variable declaration.",
                location_from_token(self.head()) if self.peek() else Location(0, 0),
            )
            return None
        self.discard()  # Discard the EQUALS token
        value: list[ASTNode] = []
        while self.tokenStream and not self.head_equals(TokenType.NEWLINE):
            self.eat_whitespace()
            node = self.parse_next()
            if node is not None:
                if not self.is_expressionable([node]):
                    self.add_error(
                        "Variable assignment value must be expressionable.",
                        node.location,
                    )
                    return None
                else:
                    value.append(node)
        return MultipleVariableSetNode(
            location_from_token(variable_token),
            variable_names,
            self.group_wrap(value),
        )

    def parse_element(self, initial_token: Token) -> ASTNode | None:
        element_name = initial_token.value
        while self.peek() and is_element_token(self.head()):
            element_name += self.pop().value

        if not self.head_is_any_of([TokenType.LEFT_PAREN, TokenType.LEFT_SQUARE]):
            return ElementNode(
                location_from_token(initial_token), element_name, [], [], []
            )

        generics = []
        if self.head_equals(TokenType.LEFT_SQUARE):
            self.discard()  # Remove the LEFT_SQUARE
            temp = self.parse_generics()
            if temp is None:
                return None
            generics = temp[0]
            self.discard()  # Remove the RIGHT_SQUARE

        if self.head_equals(TokenType.LEFT_PAREN):
            self.discard()  # Remove the LEFT_PAREN
            arguments = self.parse_element_call_syntax(element_name)
            return ElementNode(
                location_from_token(initial_token),
                element_name,
                generics,
                arguments,
                [],
            )

        return ElementNode(
            location_from_token(initial_token), element_name, generics, [], []
        )

    def parse_labelled(
        self, token: Token, ast_type: type[DuplicateNode | SwapNode | PopNode]
    ) -> ASTNode | None:
        """Parse a labelled AST node (like Duplicate, Swap, Pop)."""

        # Don't bother parsing further if there's no label indicator
        if not self.head_equals(TokenType.LEFT_SQUARE):
            return ast_type(location_from_token(token), [], [])

        self.discard()  # Discard the LEFT_SQUARE
        self.eat_whitespace()
        prestack: list[str] = []
        poststack: list[str] = []

        # Collect the prestack labels first
        while not self.head_is_any_of([TokenType.ARROW, TokenType.RIGHT_SQUARE]):
            if self.head_equals(TokenType.WORD) or self.head_equals(
                TokenType.UNDERSCORE
            ):
                prestack.append(self.pop().value)
            else:
                self.add_error(
                    "Expected label name or underscore in labelled instruction.",
                    location_from_token(self.head()) if self.peek() else Location(0, 0),
                )
                self.discard()  # Discard to try and continue
            if self.head_equals(TokenType.COMMA):
                self.discard()  # Discard the COMMA
                self.eat_whitespace()
            self.eat_whitespace()

        if self.head_equals(TokenType.RIGHT_SQUARE):
            if not prestack:
                self.add_error(
                    "Labelled instruction must have at least one prestack label if no poststack labels are provided.",
                    location_from_token(self.head()) if self.peek() else Location(0, 0),
                )
            if ast_type == PopNode:
                self.discard()  # Discard the RIGHT_SQUARE
                return ast_type(location_from_token(token), prestack, poststack)
            self.add_error(
                "Labelled instruction missing '->' for poststack labels.",
                location_from_token(self.head()) if self.peek() else Location(0, 0),
            )
            self.discard()  # Discard the RIGHT_SQUARE
            return None

        self.eat(TokenType.ARROW)
        self.eat_whitespace()
        while not self.head_equals(TokenType.RIGHT_SQUARE):
            if self.head_equals(TokenType.WORD):
                poststack.append(self.pop().value)
            else:
                self.add_error(
                    "Expected label name in post-stack labels of labelled instruction.",
                    location_from_token(self.head()) if self.peek() else Location(0, 0),
                )
                self.discard()  # Discard to try and continue
            if self.head_equals(TokenType.COMMA):
                self.discard()  # Discard the COMMA
                self.eat_whitespace()
            self.eat_whitespace()
        self.discard()  # Discard the RIGHT_SQUARE
        return ast_type(location_from_token(token), prestack, poststack)

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

    # Direct parsing methods not corresponding to AST structures
    def parse_type(self, min_precedence: int = 0) -> VTypes.VType | None:
        left = self.parse_primary_type()
        if left is None:
            return None
        self.eat_whitespace()
        while self.peek() is not None and self.peek().value in TYPE_OPERATOR_PRECEDENCE_TABLE:  # type: ignore
            operator_token = self.peek()
            assert operator_token is not None

            operator = operator_token.value
            precedence = TYPE_OPERATOR_PRECEDENCE_TABLE[operator]

            if precedence < min_precedence:
                break

            self.discard()  # Consume the operator token
            self.eat_whitespace()
            right = self.parse_type(precedence + 1)
            if right is None:
                return None

            assert left is not None
            assert right is not None

            left = self.make_type_operation(left, right, operator_token)

        if left is None:
            return None
        base_type = left
        return base_type

    def parse_primary_type(self) -> VTypes.VType | None:
        if not self.peek():
            self.add_error(
                "Unexpected end of input when parsing type.",
                Location(0, 0),
            )
            return None

        if self.head_equals(TokenType.LEFT_BRACE):
            self.discard()  # Discard the LEFT_BRACE token
            base_type = self.parse_type()
            if base_type is None:
                return None
            assert base_type is not None
            self.eat_whitespace()
            if not self.head_equals(TokenType.RIGHT_BRACE):
                self.add_error(
                    "Expected '}' after type expression.",
                    location_from_token(self.head()) if self.peek() else Location(0, 0),
                )
                return None
            self.discard()  # Discard the RIGHT_BRACE token
        else:
            name_token = self.pop()
            if (
                name_token.type != TokenType.WORD
                and name_token.type != TokenType.VARIABLE
            ):
                self.add_error(
                    f"Expected type name, got '{name_token.value}'.",
                    location_from_token(name_token),
                )
                return None

            type_name = name_token.value
            if name_token.type == TokenType.VARIABLE:
                type_name = "$" + type_name

            generic_params: Tuple[list[VTypes.VType], list[VTypes.VType]] | None = None
            self.eat_whitespace()

            if self.head_equals(TokenType.LEFT_SQUARE):
                self.discard()  # Discard LEFT_SQUARE
                if (gen := self.parse_generics()) is not None:
                    generic_params = gen
                else:
                    return None
                self.eat_whitespace()

            try:
                base_type = VTypes.type_name_to_vtype(
                    type_name, generic_params or ([], [])
                )
            except ValueError as e:
                self.add_error(
                    str(e),
                    location_from_token(name_token),
                )
                return None

        modifiers: list[TokenType] = []
        while self.head_is_any_of(
            [TokenType.PLUS, TokenType.STAR, TokenType.TILDE, TokenType.QUESTION]
        ):
            modifiers.append(self.tokenStream.pop(0).type)

        if self.head_equals(TokenType.NUMBER):
            # Handle numeric rank modifier
            number_token = self.tokenStream.pop(0)
            try:
                rank_value = int(number_token.value)
                if rank_value < 0:
                    raise ValueError("Rank value cannot be negative.")
            except ValueError:
                self.add_error(
                    f"Invalid rank value '{number_token.value}'. Must be a non-negative integer.",
                    location_from_token(number_token),
                )
                return None

            # Expand the last modifier by the numeric value
            if not modifiers:
                self.add_error(
                    "Numeric rank modifier must follow a rank modifier (+, *, ~, ?).",
                    location_from_token(number_token),
                )
                return None

            last_modifier = modifiers.pop()
            modifiers.extend([last_modifier] * rank_value)

        if not self.head_equals(TokenType.VARIABLE):
            grouped_modifiers = itertools.groupby(modifiers)
            for modifier, group in grouped_modifiers:
                count = len(list(group))  # The numeric "rank" of this type
                match modifier:
                    case TokenType.PLUS:
                        base_type = VTypes.ExactRankType(base_type, count)
                    case TokenType.STAR:
                        base_type = VTypes.MinimumRankType(base_type, count)
                    case TokenType.TILDE:
                        base_type = VTypes.ListType(base_type, count)
                    case TokenType.QUESTION:
                        for _ in range(count):
                            base_type = VTypes.OptionalType(base_type)
                    case _:
                        pass  # Will not happen, because it's guaranteed by the while condition

        elif self.head_equals(TokenType.VARIABLE):
            # Handle variable rank modifier
            var_token = self.tokenStream.pop(0)
            if not modifiers:
                self.add_error(
                    "Variable rank modifier must follow a rank modifier (+, *, ~).",
                    location_from_token(var_token),
                )
                return None

            if len(modifiers) > 1:
                self.add_error(
                    "Only one variable rank modifier is allowed.",
                    location_from_token(var_token),
                )
                return None

            if modifiers[0] != TokenType.PLUS:
                self.add_error(
                    "Only exact rank (+) modifier can be used with variable rank.",
                    location_from_token(var_token),
                )
                return None

            base_type = VTypes.ExactRankType(base_type, var_token.value)
        return base_type

    def parse_identifier(self, consider_underscore: bool = False) -> str | None:
        """
        Take the next word and just return its value as an identifier.

        :param self: This Parser instance
        :return: The identifier string
        :rtype: str
        """
        if self.head_equals(TokenType.WORD) or (
            consider_underscore and self.head_equals(TokenType.UNDERSCORE)
        ):
            token = self.tokenStream.pop(0)
            return token.value
        else:
            self.add_error(
                f"Expected identifier but got {self.peek()}",
                location=location_from_token(self.head()),
            )

    def parse_generics(self) -> Tuple[list[VType], list[VType]] | None:
        """
        Return a list of types used in a generic. Note that this is NOT for
        parsing generic declarations in things like objects/traits/etc

        Assumes that the LEFT_SQUARE has been discarded
        """

        left_side = self.parse_items(
            [TokenType.RIGHT_SQUARE, TokenType.ARROW],
            self.parse_type,
            yeet_closer=False,
        )
        if not left_side:
            return None

        self.eat_whitespace()

        right_side: list[VTypes.VType] = []

        if self.head_equals(TokenType.ARROW):
            self.discard()
            self.eat_whitespace()
            right_side = self.parse_items(
                TokenType.RIGHT_SQUARE, self.parse_type, yeet_closer=False
            )

        self.discard()

        return (left_side, right_side)

    def parse_element_call_syntax(self, element_name: str) -> list[Tuple[str, ASTNode]]:
        """
        Collect all arguments passed to an element using call syntax,
        i.e. ElementName(arg1, arg2, ...)

        Assumes that the opening LEFT_PAREN has already been consumed.

        :param self: This Parser instance
        :param initial_token: The initial token representing the element name
        :return: A list of tuples containing argument names and their corresponding ASTNodes
        """
        arguments: list[Tuple[str, ASTNode]] = []
        while not self.head_equals(TokenType.RIGHT_PAREN):
            name = ""
            if self.head_lookahead_equals([TokenType.WORD, TokenType.EQUALS]):
                name = self.pop().value
                self.eat_whitespace()
                self.discard()  # We know it's an EQUALS, because of the lookahead
                self.eat_whitespace()
            if self.head_equals(TokenType.UNDERSCORE):
                args = [ElementArgumentIgnoreNode(location_from_token(self.head()))]
                self.discard()  # Discard the UNDERSCORE
            elif self.head_equals(TokenType.HASH):
                args = [ElementArgumentFillNode(location_from_token(self.head()))]
                self.discard()  # Discard the HASH
            else:
                args = self.collect_until([TokenType.COMMA, TokenType.RIGHT_PAREN])
                if not args:
                    self.add_error(
                        f"Expected argument value in element call syntax for element '{element_name}'.",
                        location_from_token(self.head()),
                    )
                    return []
                if not self.is_expressionable(args):
                    self.add_error(
                        f"Element call syntax arguments must be expressionable for element '{element_name}'.",
                        location_from_token(self.head()),
                    )
                    return []
            argument_node = self.group_wrap(args)  # type: ignore
            arguments.append((name, argument_node))
            self.eat_whitespace()
            if self.head_equals(TokenType.COMMA):
                self.discard()
                self.eat_whitespace()
            elif not self.head_equals(TokenType.RIGHT_PAREN):
                self.add_error(
                    f"Expected ',' or ')' in element call syntax for element '{element_name}'.",
                    location_from_token(self.head()),
                )
                return []
        self.discard()  # Discard the RIGHT_PAREN
        return arguments

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

    def is_dictionary_item(self, node: ASTNode):
        """
        Check whether the provided ASTNode list represents a valid dictionary key.
        :param self: This Parser instance
        :param nodes: List of ASTNodes to check
        :type nodes: list[ASTNode]
        :return: ReturnValue indicating whether the nodes form a valid dictionary key
        :rtype: ReturnValue
        """

        # If it is not a GroupNode, it cannot be a dictionary key,
        # as it is only a single item. Therefore, return NO if it is
        # expressionable, ERROR otherwise.
        if not isinstance(node, GroupNode):
            if self.is_expressionable([node]):
                return DictCheckReturnValue.NO
            else:
                self.add_error(
                    "Expressionable item found when parsing list/dictionary.",
                    node.location,
                )
                return DictCheckReturnValue.ERROR

        nodes = node.elements[::]

        # Collect expressionable nodes from the start
        # which will either get us to the end (NO) or
        # something that could be the "=" that makes this
        # a dictionary item.
        while nodes and self.is_expressionable([nodes[0]]):
            nodes.pop(0)

        if not nodes:
            return DictCheckReturnValue.NO

        if not isinstance(nodes[0], AuxiliaryTokenNode):
            self.add_error(
                "Expected '=' or expressionable item when parsing list/dictionary.",
                nodes[0].location,
            )
            return DictCheckReturnValue.ERROR  # Not an "=" token, so ERROR

        if nodes[0].token.type != TokenType.EQUALS:
            self.add_error(
                "Expected '=' token or expressionable item when parsing list/dictionary.",
                nodes[0].location,
            )
            return DictCheckReturnValue.ERROR  # Not an "=" token, so ERROR

        nodes.pop(0)  # Remove the "=" token

        # Don't return yet because we need to make sure it's a valid
        if not nodes:
            self.add_error(
                "Expected value after '=' in dictionary item.",
                node.location,
            )
            return DictCheckReturnValue.ERROR

        while nodes and self.is_expressionable([nodes[0]]):
            nodes.pop(0)

        if not nodes:
            return DictCheckReturnValue.YES
        self.add_error(
            "Unexpected token after dictionary item value.",
            nodes[0].location,
        )

        return DictCheckReturnValue.ERROR

    def parse_list_item(self) -> ASTNode | None:
        """
        A helper function for list parsing that turns isolated "="s
        into auxiliary token ASTNodes. This is so that dictionary-ness
        can even be determined.

        If the first token is not an "=", just parse normally.

        This is a class method because the parse_items method does
        not take a function that takes any parameters other than self.
        So therefore, this function needs to be able to mutate self.

        :param self: This Parser instance
        :return: The parsed ASTNode
        """

        if self.tokenStream and self.tokenStream[0].type == TokenType.EQUALS:
            equals_token = self.tokenStream.pop(0)
            return AuxiliaryTokenNode(location_from_token(equals_token), equals_token)
        return self.parse_next()

    def extract_dict_items(self, group_node: GroupNode) -> Tuple[ASTNode, ASTNode]:
        """
        Given a GroupNode that represents a dictionary item,
        extract and return the key and value ASTNodes.

        :param self: This Parser instance
        :param group_node: The GroupNode representing the dictionary item
        :type group_node: GroupNode
        :return: A tuple containing the key and value ASTNodes
        :rtype: Tuple[ASTNode, ASTNode]
        """
        nodes = group_node.elements[::]

        key_nodes: list[ASTNode] = []
        while nodes and self.is_expressionable([nodes[0]]):
            key_nodes.append(nodes.pop(0))

        key_node = self.group_wrap(key_nodes)

        # Remove the "=" token
        if nodes and isinstance(nodes[0], AuxiliaryTokenNode):
            nodes.pop(0)

        value_nodes: list[ASTNode] = []
        while nodes:
            value_nodes.append(nodes.pop(0))

        value_node = self.group_wrap(value_nodes)

        return (key_node, value_node)

    def make_type_operation(
        self, left: VTypes.VType, right: VTypes.VType, operator_token: Token
    ) -> VTypes.VType | None:
        """
        Given two VTypes and an operator token, create and return
        the resulting VType from applying the operator.

        :param self: This Parser instance
        :param left: The left-hand side VType
        :type left: VTypes.VType
        :param right: The right-hand side VType
        :type right: VTypes.VType
        :param operator_token: The operator token
        :type operator_token: Token
        :return: The resulting VType after applying the operator, or None on error
        :rtype: VTypes.VType | None
        """
        operator = operator_token.value
        match operator:
            case "&":
                return VTypes.IntersectionType(left, right)
            case "|":
                return VTypes.UnionType(left, right)
            case _:
                self.add_error(
                    f"Unknown type operator '{operator}'.",
                    location_from_token(operator_token),
                )
                return None
