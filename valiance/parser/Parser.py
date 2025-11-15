import itertools
from string import whitespace
from typing import Callable, Tuple, TypeVar

import valiance.vtypes.VTypes as VTypes
from valiance.lexer.Token import Token
from valiance.lexer.TokenType import TokenType
from valiance.parser.AST import (
    ASTNode,
    AugmentedVariableSetNode,
    DuplicateNode,
    ElementNode,
    GroupNode,
    ListNode,
    LiteralNode,
    SwapNode,
    TupleNode,
    VariableGetNode,
    VariableSetNode,
)

T = TypeVar("T")
U = TypeVar("U")


def DUMMY_WRAP_FN(x: list[T]) -> T:
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
            case TokenType.LEFT_SQUARE:  # List literal
                list_elements = self.parse_list()
                return ListNode(list_elements)
            case TokenType.LEFT_BRACE:  # Block / group
                group_elements = self.parse_block()
                return GroupNode(group_elements)
            case TokenType.LEFT_PAREN:  # Tuple
                tuple_elements = self.parse_tuple()
                return TupleNode(tuple_elements)
            case TokenType.VARIABLE:
                # There's three cases when a variable token is encountered.
                # First is when the variable is followed immediately by an EQUALS token,
                # indicating a variable assignment. Everything up until the next line
                # or EOF is considered the value to assign.
                # The second is when the variable is followed by a COLON token,
                # indicating an augmented assignment. Everything up until the next line
                # or EOF is considered the function to augment with.
                # The third is when neither of those tokens follow, indicating a variable retrieval.

                # Important to eat any whitespace before checking the next token.
                # $name = value #: Completely valid, and aesthetically preferable.
                self.eat_whitespace()

                # Variable Assignment
                if self.head_equals(TokenType.EQUALS) and not self.token_at_equals(
                    1, TokenType.EQUALS
                ):  # Make sure that the = isn't part of == or ===
                    self.discard()  # Discard the EQUALS token
                    value: list[ASTNode] = []

                    # Parse ASTs until NEWLINE or EOF
                    while not self.head_equals(
                        TokenType.NEWLINE
                    ) and not self.head_equals(TokenType.EOF):
                        node = self.parse_next()
                        if node is not None:
                            value.append(node)
                    if value:
                        return VariableSetNode(token.value, self.group_wrap(value))
                    else:
                        raise Exception(
                            f"Expected value after '=' for variable '{token.value}' at line {token.line}, column {token.column}"
                        )

                # Variable Augmented Assignment
                elif self.head_equals(TokenType.COLON):
                    self.discard()  # Discard the COLON token
                    fn = self.parse_next()
                    if fn is not None:
                        return AugmentedVariableSetNode(token.value, fn)
                    else:
                        raise Exception(
                            f"Expected function after ':' for augmented variable '{token.value}' at line {token.line}, column {token.column}"
                        )
                # Variable Retrieval
                else:
                    return VariableGetNode(token.value)
            case _ if token.type == TokenType.WORD or is_element_token(token):
                return self.parse_element(token)
            case TokenType.DUPLICATE:
                # Two cases: labelled duplication and unlabelled duplication

                # Labelled duplication is of the form:
                # ^[stackstate -> newstackstate]
                if self.head_equals(TokenType.LEFT_SQUARE):
                    self.discard()  # Discard LEFT_SQUARE
                    # Collect pre-stack and post-stack labels
                    pre_labels = self.parse_items(
                        TokenType.ARROW,
                        self.parse_identifier,
                        conglomerate=False,
                    )
                    post_labels = self.parse_items(
                        TokenType.RIGHT_SQUARE,
                        self.parse_identifier,
                        conglomerate=False,
                    )
                    return DuplicateNode(pre_labels, post_labels)
                else:
                    # Unlabelled duplication
                    return DuplicateNode([], [])
            case TokenType.SWAP:
                # Like duplication, two cases: labelled and unlabelled

                # Labelled swap is of the form:
                # \[prestack -> poststack]
                if self.head_equals(TokenType.LEFT_SQUARE):
                    self.discard()  # Discard LEFT_SQUARE

                    # Collect pre-stack and post-stack labels
                    pre_labels = self.parse_items(
                        TokenType.ARROW,
                        self.parse_identifier,
                        conglomerate=False,
                    )
                    post_labels = self.parse_items(
                        TokenType.RIGHT_SQUARE,
                        self.parse_identifier,
                        conglomerate=False,
                    )
                    return SwapNode(pre_labels, post_labels)
                else:
                    # Unlabelled swap
                    return SwapNode([], [])
            case TokenType.EOF:
                return None
            case _:
                raise Exception(
                    f"Unexpected token {token.type} at line {token.line}, column {token.column}"
                )
        return None

    def parse_identifier(self) -> str:
        """
        Take the next word and just return its value as an identifier.

        :param self: This Parser instance
        :return: The identifier string
        :rtype: str
        """
        if self.head_equals(TokenType.WORD):
            token = self.tokenStream.pop(0)
            return token.value
        else:
            raise Exception(f"Expected identifier but got {self.peek()}")

    def parse_list(self) -> list[ASTNode]:
        """
        Parse a list of AST nodes enclosed in square brackets.

        :param self: This Parser instance
        :return: A list of AST nodes
        :rtype: list[ASTNode]
        """
        return self.parse_items(
            TokenType.RIGHT_SQUARE,
            self.parse_next,
            conglomerate=True,
            wrap_fn=self.group_wrap,
            separator=TokenType.COMMA,
        )

    def parse_block(self) -> list[ASTNode]:
        """
        Parse a block of AST nodes enclosed in braces.
        Acts only as a grouping mechanism. No scoping.

        :param self: This Parser instance
        :return: A list of AST nodes
        :rtype: list[ASTNode]
        """
        return self.parse_items(
            TokenType.RIGHT_BRACE, self.parse_next, wrap_fn=self.group_wrap
        )

    def parse_tuple(self) -> list[ASTNode]:
        """
        Parse a tuple of AST nodes enclosed in parentheses.

        :param self: This Parser instance
        :return: A list of AST nodes
        :rtype: list[ASTNode]
        """
        return self.parse_items(
            TokenType.RIGHT_PAREN,
            self.parse_next,
            conglomerate=True,
            wrap_fn=self.group_wrap,
            separator=TokenType.COMMA,
        )

    def parse_element(self, first_token: Token) -> ASTNode:
        """
        Parse an element starting with the name starting with first_token.

        Will parse any generics and arguments following the element name.

        :param self: This Parser instance
        :param first_token: The first token of the element
        :type first_token: Token
        :return: An AST node representing the element
        :rtype: ASTNode
        """

        # Retrieve the initial element name fragment. This is crucial
        # because the token stream has already removed this first token.
        # Trying to collect WORD tokens from this point would miss it.
        element_name = first_token.value

        # Collect the rest of the element name from subsequent element
        # tokens.
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

        # Finally, check to see if this element is modified
        # with `:`.

        # Modifier checking is performed in the element parsing function,
        # rather than in parse_next, to (hopefully) simplify the program
        # analysis stage. The idea, in theory, is that a modified element
        # can first determine its overload from stack args + function-taking
        # overloads, and _then_ determine how many elements it'll take.

        modified = False
        self.eat_whitespace()
        if self.head_equals(TokenType.COLON):
            modified = True
            self.discard()  # Remove the modifier token

        return ElementNode(element_name, generics, arguments, modified)

    def parse_type_parameters(self) -> list[VTypes.VType]:
        """
        Parse type parameters enclosed in square brackets.

        :param self: This Parser instance
        :return: A list of type parameters
        :rtype: list[VType]
        """
        generics: list[VTypes.VType] = []
        self.discard()  # Discard the LEFT_SQUARE

        generics = self.parse_items(
            TokenType.RIGHT_SQUARE,
            self.parse_type,
            conglomerate=False,
            separator=TokenType.COMMA,
        )

        self.discard()  # Discard the RIGHT_SQUARE
        return generics

    def parse_type(self) -> VTypes.VType:
        """
        Parse a type.

        :param self: This Parser instance
        :return: A VType representing the parsed type
        :rtype: VType
        """

        # This is technically the "intersection type" parser,
        # but it's called parse_type to be the entry point for type parsing.

        lhs = self.parse_union_type()
        self.eat_whitespace()
        if self.head_equals(TokenType.AMPERSAND):
            self.discard()  # Discard the AMPERSAND
            self.eat_whitespace()
            rhs = self.parse_union_type()
            return VTypes.IntersectionType(lhs, rhs)
        return lhs

    def parse_union_type(self) -> VTypes.VType:
        """
        Parse a union type. Part of parse_type, needed to handle precedence.

        :param self: This Parser instance
        :return: A VType representing the parsed union type
        :rtype: VType
        """

        lhs = self.parse_primary_type()
        self.eat_whitespace()
        if self.head_equals(TokenType.PIPE):
            self.discard()  # Discard the PIPE
            self.eat_whitespace()
            rhs = self.parse_primary_type()
            return VTypes.UnionType(lhs, rhs)
        return lhs

    def parse_primary_type(self) -> VTypes.VType:
        """
        Parse a "primary" type, i.e., a base type with any modifiers.
        Not an intersection or union type.

        :param self: This Parser instance
        :return: A VType representing the parsed primary type
        :rtype: VType
        """

        # The generated type is constructed as a combination
        # of base type and type modifiers.

        # First, the base type
        base_type: VTypes.VType = VTypes.VType()
        if self.head_equals(TokenType.WORD):  # The case that it's a named type
            type_token = self.tokenStream.pop(0)
            # Check for built-in types
            # Especially important for Dictionary and Function types, which
            # require special parsing.
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
                    self.eat_whitespace()

                    key_type = self.parse_type()
                    self.eat_whitespace()

                    if not self.head_equals(TokenType.ARROW):
                        raise Exception("Expected '->' in Dictionary type declaration.")

                    self.discard()  # Discard the ARROW
                    self.eat_whitespace()

                    value_type = self.parse_type()
                    base_type = VTypes.DictionaryType(key_type, value_type)
                    self.eat_whitespace()

                    if not self.head_equals(TokenType.RIGHT_SQUARE):
                        raise Exception(
                            "Expected ']' at the end of Dictionary type declaration."
                        )
                    self.discard()  # Discard RIGHT_SQUARE
                case "Function":
                    # Delegated to another function because it's more complex
                    # than this match statement should handle.
                    base_type = self.parse_function_type(function_token_skipped=True)
                case _:
                    # Custom type
                    # Check to see if it has any type parameters (i.e. generics)
                    # An empty list means no generics.
                    type_parameters: list[VTypes.VType] = []
                    if self.head_equals(TokenType.LEFT_SQUARE):
                        type_parameters = self.parse_type_parameters()
                    base_type = VTypes.CustomType(type_token.value, type_parameters)
        elif self.head_equals(TokenType.LEFT_PAREN):  # Tuple type
            self.discard()  # Discard LEFT_PAREN
            element_types: list[VTypes.VType] = self.parse_items(
                TokenType.RIGHT_PAREN, self.parse_type, conglomerate=False
            )
            self.discard()  # Discard RIGHT_PAREN
            base_type = VTypes.TupleType(element_types)
        else:
            raise Exception(
                f"Expected a primary type, but got {self.tokenStream[0].type if self.tokenStream else 'end of input'}"
            )

        # Now, the list rank modifiers
        # These are:
        #  + (ExactRankType)
        #  * (MinimumRankType)
        #  ~ (ListType)
        # This is a two step process. First, collect all the modifiers.
        # Then, run-length encode them into the base type.
        modifiers: list[TokenType] = []
        while self.head_is_any_of([TokenType.PLUS, TokenType.STAR, TokenType.TILDE]):
            modifiers.append(self.tokenStream.pop(0).type)

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
                case _:
                    pass  # Will not happen, because it's guaranteed by the while condition

        # Finally, wrap the base type in as many Optionals as there are QUESTION tokens
        while self.head_equals(TokenType.QUESTION):
            self.discard()  # Discard QUESTION
            base_type = VTypes.OptionalType(base_type)

        return base_type

    def parse_function_type(self, function_token_skipped: bool = False) -> VTypes.VType:
        """
        Parse the parameters and return types of a function type.

        :param self: This Parser instance
        :param function_token_skipped: Whether previous parsing has already consumed the 'Function' token
        :type function_token_skipped: bool
        :return: A VType representing the parsed function type
        :rtype: VType
        """

        # Sometimes, the 'Function' token has already been consumed
        # by previous parsing logic. In that case, we don't want
        # to discard it again.
        if not function_token_skipped:
            self.discard()  # Discard FUNCTION token
        self.eat_whitespace()

        if not self.head_equals(TokenType.LEFT_SQUARE):
            raise Exception("Expected '[' at the start of function type parameters.")

        param_types: list[VTypes.VType] = []
        self.discard()  # Discard LEFT_SQUARE
        self.eat_whitespace()

        if self.head_equals(TokenType.RIGHT_SQUARE):
            # A function type with no parameters and no return types
            # 99% of the time, this will be used in @stack elements.
            # The other 1% of the time will be a compile error during
            # program analysis.
            self.discard()  # Discard RIGHT_SQUARE
            self.eat_whitespace()
            return VTypes.FunctionType(False, [], [], [], [])

        param_types = self.parse_items(
            TokenType.ARROW, self.parse_type, conglomerate=False
        )

        self.eat_whitespace()
        return_types: list[VTypes.VType] = self.parse_items(
            TokenType.RIGHT_SQUARE, self.parse_type, conglomerate=False
        )
        # TODO: Where clauses
        return VTypes.FunctionType(True, [], param_types, return_types, [])

    def parse_element_arguments(self) -> list[Tuple[str, ASTNode]]:
        """
        Parse the arguments of an element. Note that this needs to be
        more complex than just using parse_items, because arguments
        can be named.

        Unnamed arguments will have an empty string as their name.

        :param self: This Parser instance
        :return: A list of tuples, each containing an argument name and its corresponding ASTNode
        :rtype: list[Tuple[str, ASTNode]]
        """
        arguments: list[Tuple[str, ASTNode]] = []
        self.discard()  # Discard LEFT_PAREN

        while not self.head_equals(TokenType.RIGHT_PAREN):
            self.eat_whitespace()
            arg_name = ""  # Start out with the assumption that the argument is unnamed
            elements: list[ASTNode] = (
                []
            )  # A list, because the argument may be like 3 4 +

            if self.head_equals(TokenType.WORD):
                # A word token means it's _possible_ that this is a named argument.
                # So check ahead to see if the next non-whitespace token is an EQUALS.
                # HOWEVER. The whitespace consumption can't be done using eat_whitespace,
                # because that destroys the whitespace. This is problematic because
                # two WORD tokens separated by whitespace will be otherwise mashed
                # together.

                temp_token = self.tokenStream.pop(0)
                whitespace_tokens: list[Token] = []

                # Do the safe whitespace consumption
                while self.head_equals(TokenType.WHITESPACE):
                    whitespace_tokens.append(self.tokenStream.pop(0))

                if self.head_equals(TokenType.EQUALS):
                    # Definitely a named argument
                    # The whitespace list can be ignored
                    arg_name_token = temp_token
                    arg_name = arg_name_token.value
                    self.discard()  # Discard EQUALS
                else:
                    # Not a named argument. Restore the whitespace tokens
                    for ws_token in reversed(whitespace_tokens):
                        self.tokenStream.insert(0, ws_token)
                    elements.append(self.parse_element(temp_token))

            # From here, just collect elements until a COMMA or RIGHT_PAREN
            # The name has already been determined to either be empty or set.
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

    def parse_items(
        self,
        close_token: TokenType,
        parse_fn: Callable[[], T | None],
        conglomerate: bool = False,  # Whether to wrap items in a GroupNode if multiple
        wrap_fn: Callable[
            [list[T]], T
        ] = DUMMY_WRAP_FN,  # Function to wrap conglomerate items
        separator: TokenType = TokenType.COMMA,
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
        :return: The list of parsed items, possibly wrapped if conglomerate is True
        :rtype: list[T]
        """
        items: list[T] = []  # The collected items
        current_item: list[T] = []  # Used to collect items before wrapping

        # Editor's note: I am unsure as to whether this is the minimum
        # number of whitespace consumptions needed. It works, but there's
        # a slight chance at least one can be safely removed.

        # The thinking is that:
        # 1. Whitespace needs to be consumed before checking for the loop entry.
        #    [   ] is valid, so leading whitespace before the close_token
        #    needs to be eaten.
        # 2. Whitespace needs to be consumed before checking for a separator.
        #    [item , item] is valid, so whitespace before the separator
        #    needs to be eaten.
        # 3. Whitespace after the separator might not need to be consumed,
        #    BUT, the parse_fn might not handle leading whitespace itself,
        #    so it'll need to be consumed here.
        # 4. Finally, before the next check of the close token, whitespace
        #    needs to be consumed again.
        # In conclusion, all whitespace consumptions are necessary.
        # I leave this here as a note for anyone (most likely me) ponders
        # whether 4 whitespace consumptions is excessive (it isn't).

        self.eat_whitespace()  # Consumption 1 - Pre-loop

        while not self.head_equals(close_token):
            self.eat_whitespace()  # Consumption 2 - Pre-separator

            if self.head_equals(separator):
                if conglomerate:
                    if not current_item:
                        raise Exception("Empty item detected.")
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
