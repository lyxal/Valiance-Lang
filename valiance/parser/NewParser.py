from abc import abstractmethod
from typing import Callable, Optional, TypeVar

from valiance.parser.Errors import GenericParseError, ParserError

from valiance.parser.AST import *
from valiance.lexer.Token import Token
from valiance.lexer.TokenType import TokenType
from valiance.vtypes import VTypes

T = TypeVar("T")
U = TypeVar("U")

TYPE_OPERATOR_PRECEDENCE_SET = [{"|"}, {"&"}]
TYPE_OPERATOR_PRECEDENCE_TABLE: dict[str, int] = {}
for precedence, operators in enumerate(TYPE_OPERATOR_PRECEDENCE_SET):
    for operator in operators:
        TYPE_OPERATOR_PRECEDENCE_TABLE[operator] = precedence

# A mapping of opening tokens to their corresponding closing tokens
OPEN_CLOSE_TOKEN_MAP: dict[TokenType, TokenType] = {
    TokenType.LEFT_PAREN: TokenType.RIGHT_PAREN,
    TokenType.LEFT_BRACE: TokenType.RIGHT_BRACE,
    TokenType.LEFT_SQUARE: TokenType.RIGHT_SQUARE,
}

# A helper function to generate a depth-tracking table for
# token synchronisation.
sync_table = lambda: {_type: 0 for _type in OPEN_CLOSE_TOKEN_MAP}


def is_element_token(token: Token) -> bool:
    """Determine if a token can be used in an element name

    Args:
        token (Token): The token to check

    Returns:
        bool: Whether the token can be used in an element name
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


class ParserStrategy:
    """A base class for all parser strategies. Do NOT ever create instances of
    this class. Instead, subclass it and implement the abstract methods.

    Takes a Parser instance as an argument to the constructor. Access the parser
    via self.parser.
    """

    name: str = "UnnamedStrategy"

    def __init__(self, parser: Parser):
        self.parser = parser

    @abstractmethod
    def can_parse(self) -> bool:
        """Return whether this parsing strategy is able to be called

        Returns:
            bool: Whether this parsing strategy is applicable
        """
        pass

    def go(self, *token_types: TokenType) -> bool:
        """A shortcut way to tell if a strategy is parsable from just checking
        the first token in the parser's token stream.

        Useful for when the condition in `can_parse` would otherwise
        be `self.parser.head_in(...)`

        Args:
            *token_types (TokenType): The token types to check for

        Returns:
            bool: Whether the first token matches any of the given token types
        """
        for ind, token_type in enumerate(token_types):
            if (head_token := self.parser.peek(ind)) is None:
                return False
            if head_token.type != token_type:
                return False
        return True

    @abstractmethod
    def parse(self) -> ASTNode:
        pass

    def sync_and_exit(self, *token_types: TokenType) -> ErrorNode:
        self.parser.sync(*token_types)
        return ErrorNode(
            self.parser.head().location,
            self.parser.head_opt() or Token(TokenType.EOF, "", -1, -1),
        )


class Parser:
    def __init__(self, tokens: list[Token]):
        self.asts: list[ASTNode] = []

        # Track errors encountered while using a strategy
        self.error_stack: list[list[GenericParseError]] = []

        # All errors encountered during parsing
        self.errors: list[Tuple[str, list[GenericParseError]]] = []

        self.strategies: list[ParserStrategy] = []
        self.tokens = tokens

        self._collect_strategies()

    def _collect_strategies(self) -> None:
        # Collect all ParserStrategy subclasses defined in this module
        for subclass in ParserStrategy.__subclasses__():
            self.strategies.append(subclass(self))

    def add_error(self, message: str, location: Optional[Token]) -> None:
        """Add an error to the current error stack

        Args:
            message (str): The error message to display
            location (Optional[Token]): The location of the error. Will default to (-1, -1) [e.g. when EOF is reached]
        """
        if location is not None:
            self.error_stack[-1].append(GenericParseError(message, location.location))
        else:
            self.error_stack[-1].append(GenericParseError(message, Location(-1, -1)))

    def add_global_error(self, message: str, location: Optional[Token]) -> None:
        """Add an error to the global list of errors. Helpful for when there is
        an error that isn't from any given strategy.

        Args:
            message (str): The error message to display
            location (Optional[Token]): Error token.
        """
        if location is not None:
            self.errors.append(
                (
                    "Global",
                    [GenericParseError(message, location.location)],
                )
            )
        else:
            self.errors.append(
                (
                    "Global",
                    [GenericParseError(message, Location(-1, -1))],
                )
            )

    def discard(self, number_of_tokens: int = 1) -> None:
        """Remove the first n items from the head of the token stream.

        Args:
            number_of_tokens (int, optional): The number of tokens to remove. Defaults to 1.
        """
        self.tokens = self.tokens[number_of_tokens:]

    def eat(self, token_type: TokenType, message: Optional[str] = None) -> bool:
        """Expect and consume a token of a given type. If the head of the token
        stream is not as expected, then a parser error is added.

        Args:
            token_type (TokenType): The expected token type
            message (Optional[str], optional): A message to use if the default error message isn't desired. Defaults to None.

        Returns:
            bool: Whether the expected token was found and consumed. False if an error was added.
        """

        self.error_if_eof(f"Expected {token_type}, but found end of input.")

        # No need to eat whitespace here; head_equals does that for us
        if self.head_equals(token_type):
            self.discard()
            return True
        else:
            self.add_error(
                message
                or f"Expected token of type {token_type}, but found {self.head().type}.",
                self.head(),
            )
            return False

    def eat_whitespace(self) -> None:
        """Discard all leading whitespace before the next token.

        NOTE: In practice, this should NOT need to be called manually.
        If you find yourself needing to call this, consider whether the
        parser strategy you are implementing is correctly eating whitespace.
        """

        # VERY IMPORTANT: The eat_whitspace parameter MUST be set to False
        # because otherwise you get some very silly infinite recursion.

        # The above may or may not have been learned the hard way.

        while self.head_equals(TokenType.WHITESPACE, eat_whitespace=False):
            self.discard()

    def error_if_eof(self, message: Optional[str] = None) -> None:
        """Raise an error if the token stream is at EOF.

        Considers the parser to be at EOF if there are no non-whitespace tokens
        remaining.

        NOTE: This should usually be caught by the `parse_next` method. If
        this goes uncaught, something has gone very wrong.

        Because it's intended to be caught, the parser error is not added
        here. The error will be added in `parse_next`. Again, if this goes
        uncaught by `parse_next`, something has gone very wrong.

        Args:
            message (Optional[str], optional): _description_. Defaults to None.

        Raises:
            IndexError: _description_
        """

        self.eat_whitespace()
        if not self.tokens:
            raise ParserError(message or "Unexpected end of input.")

    def head(self) -> Token:
        """Get the next token without consuming it.

        Returns:
            Token: The next token in the stream.
        """
        self.error_if_eof()
        return self.tokens[0]

    def head_equals(self, token_type: TokenType, eat_whitespace: bool = True) -> bool:
        """Check if the next token is of the given type.

        Args:
            token_type (TokenType): The token type to check for
            eat_whitespace (bool, optional): Whether whitespace should be consumed before checking. Defaults to True.

        Returns:
            bool: Whether the next token is of the given type.
        """

        # If no whitespace is to be eaten, don't check for EOF
        # that's because it'll recurse infinitely.
        if eat_whitespace:
            self.eat_whitespace()
            self.error_if_eof()
        return self.tokens[0].type == token_type

    def head_in(self, *token_types: TokenType, eat_whitespace: bool = True) -> bool:
        """Check if the next token is in the given set of types.

        Args:
            *token_types (TokenType): The token types to check for
            eat_whitespace (bool, optional): Whether whitespace should be consumed before checking. Defaults to True.

        Returns:
            bool: Whether the next token is in the given set of types.
        """
        if eat_whitespace:
            self.eat_whitespace()
            self.error_if_eof()
        return self.tokens[0].type in token_types

    def head_opt(self) -> Optional[Token]:
        """Safely get the next token.

        There's a very good chance that this method isn't needed at all,
        because the parser should probably never be in a state where there
        are no tokens left to parse and this method is called.

        Might delete later. So probably don't use this. /shrug

        Returns:
            Optional[Token]: The next token, or None if at EOF.
        """
        if not self.tokens:
            return None
        return self.tokens[0]

    def lookahead_equals(
        self, token_types: list[TokenType], eat_whitespace: bool = True
    ) -> bool:
        """Check whether the start of the lookahead matches a given sequence of tokens

        Args:
            token_types (list[TokenType]): The sequence of token types to check for
            eat_whitespace (bool, optional): Whether whitespace should be consumed before checking. Defaults to True.

        Returns:
            bool: Whether the lookahead matches the given sequence of token types.
        """
        if eat_whitespace:
            self.eat_whitespace()
            self.error_if_eof()
        for i, token_type in enumerate(token_types):
            if len(self.tokens) <= i or self.tokens[i].type != token_type:
                return False
        return True

    def sync(self, *token_types: TokenType) -> None:
        """Synchronise the parser to the next occurrence of any of the given token types,
        accounting for the fact that nesting may occur.

        NOTE: Does NOT consume the synchronisation token. The parser will be left
        positioned at the synchronisation token, ready for the parsing strategy
        to resume.

        Args:
            *token_types (TokenType): The token types to synchronise to
        """

        if not token_types:
            raise ValueError(
                "What. Are you have the stupid? Braindeadmaxxing? You goofy ahh need to give me tokens to sync to. Dingus."
            )

        self.error_if_eof()

        # Initialise the open/close depth tracking table
        open_close_count = sync_table()
        while self.tokens:
            if self.head().type in token_types and all(
                count == 0 for count in open_close_count.values()
            ):
                # Only stop syncing if we're at depth 0 for all open/close pairs
                return
            if self.head().type in OPEN_CLOSE_TOKEN_MAP:
                open_close_count[self.head().type] += 1
            elif self.head().type in OPEN_CLOSE_TOKEN_MAP.values():
                corresponding_open = [
                    k for k, v in OPEN_CLOSE_TOKEN_MAP.items() if v == self.head().type
                ][0]
                if open_close_count[corresponding_open] > 0:
                    open_close_count[corresponding_open] -= 1
                else:
                    return
            self.discard()

    def peek(self, offset: int = 1) -> Optional[Token]:
        """Return the token at the given offset without consuming it.

        Args:
            offset (int, optional): The number of tokens to look ahead. Defaults to 1.

        Raises:
            ValueError: If the offset is negative.
            IndexError: If there are no more tokens available when offset is 1.

        Returns:
            Optional[Token]: The token at the given offset, or None if not available.
        """
        if offset < 0:
            raise ValueError("Offset must be non-negative.")
        if offset == 1 and not self.tokens:
            raise IndexError("No more tokens available.")
        if len(self.tokens) <= offset:
            return None
        return self.tokens[offset]

    def pop(self) -> Token:
        """Consume and return the next token. Different to `discard` in that
        the token is returned. Different to `head` in that the token is consumed.
        Different to `eat` in that no type checking is performed.

        Returns:
            Token: The next token in the stream.
        """
        self.error_if_eof()
        token = self.tokens[0]
        self.discard()
        return token

    def parse_items(
        self,
        OPEN: TokenType,
        SEP: TokenType,
        CLOSE: TokenType,
        parse_function: Callable[[], T],
        is_error: Callable[[T], bool],
        error_function: Callable[[Token], T],
        singleton: bool = False,
        validate: Optional[Callable[[T], bool]] = None,
        multi_item_wrap: Callable[[list[T]], T] = lambda items: items[0],
        *sync_set: TokenType,
    ) -> list[T]:
        """Parse a collection of items, enclosed by OPEN and CLOSE tokens, separated by SEP tokens.
        Optionally, validate each item using the provided validate function.
        Also optionally, enforce that each item contains only a single element if singleton is True.

        Notes:

        - Assumes that the caller has already eaten any leading whitespace.
        - Assumes that OPEN has _not_ been consumed yet.
        - Does NOT consume the CLOSE token.
        - Can be used to parse sequences of ASTs, Identifiers, Types, etc.
        - It is the caller's responsibility to verify whether emptiness is allowed
        - It is also the caller's responsibility to wrap items in appropriate AST nodes if needed. (E.G. as GroupASTNodes)

        Args:
            OPEN (TokenType): The token type that opens the collection.
            SEP (TokenType): The token type that separates items in the collection.
            CLOSE (TokenType): The token type that closes the collection.
            parse_function (Callable[[], T]): The parse function to call for each item. Usually will be parse_next
            is_error (Callable[[T], bool]): A function to determine if a parsed item is an error.
            error_function (Callable[[Token], T]): A function to generate the value to use for items that fail validation OR return an error. Usually will be an ErrorNode or similar.
            singleton (bool, optional): Whether to enforce that each item contains only a single element. Defaults to False.
            validate (Optional[Callable[[T], bool]], optional): A function to validate each item. Defaults to None.
            multi_item_wrap (Callable[[list[T]], T], optional): A function to wrap multiple items into a single item. Defaults to lambda items: items.

        Returns:
            list[T]: The parsed items
        """

        items: list[T] = []
        self.eat(OPEN)
        if self.head_equals(CLOSE):
            return items

        while not self.head_equals(CLOSE):
            item_set: list[T] = []
            while not (self.head_equals(SEP) or self.head_equals(CLOSE)):
                item = parse_function()
                if validate is not None and not validate(item):
                    self.add_error(
                        f"Invalid item when parsing items. Found {item}.", self.head()
                    )
                    self.sync(SEP, CLOSE, *sync_set)
                    items.append(error_function(self.head()))
                    break
                # If any item is an error, propagate the error
                # Two different checks to handle both value and identity comparisons
                # Just in case there's any funky comparison logic in use
                if is_error(item):
                    items.append(item)
                    self.add_error(
                        f"Error encountered when parsing items. Found {item}.",
                        self.head(),
                    )
                    self.sync(SEP, CLOSE, *sync_set)
                    break
                item_set.append(item)
            # Now that we're at the SEP (or CLOSE), enforce singleton if needed
            if singleton:
                if len(item_set) != 1:
                    self.add_error(
                        f"Expected a single item in this position, but found {len(item_set)}.",
                        self.head(),
                    )
                    items.append(error_function(self.head()))
                else:
                    items.append(item_set[0])
            else:
                if item_set:
                    items.append(multi_item_wrap(item_set))
            if not self.head_equals(CLOSE):
                if not self.eat(
                    SEP,
                    f"Expected '{SEP.name}' between items. Found '{self.head().type.name}' instead. Notably, this error should never occur. If you're reading this as an error, then something has gone very wrong.",
                ):
                    self.sync(SEP, CLOSE, *sync_set)
        return items

    def parse(self) -> list[ASTNode]:
        """Parse the tokens into AST nodes.

        Returns:
            list[ASTNode]: The parsed AST nodes.
        """
        while self.tokens and not self.head_equals(TokenType.EOF):
            ast = self.parse_next()
            self.asts.append(ast)
        return self.asts

    def parse_next(self) -> ASTNode:
        """Parse the next item from the token stream.

        Checks the head of the token stream against all defined strategies.

        NOTE: Order of strategy evaluation is not guaranteed, so make
        sure that strategies are mutually exclusive.

        Returns:
            ASTNode: The parsed AST node.
        """

        print("Parsing next token:", self.head())
        print("Remaining tokens:", self.tokens)

        for strategy in self.strategies:
            if strategy.can_parse():
                # Wrap in a try/except to catch any errors that aren't
                # simple parse errors or things that a strategy should handle.
                # (for example, IndexErrors from popping from an empty token list
                # or other errors that are implicitly checked for by the parser.)
                try:
                    self.error_stack.append([])
                    result = strategy.parse()
                    # If there were errors during parsing, add them to the main error list
                    if self.error_stack[-1]:
                        self.errors.append((strategy.name, self.error_stack[-1]))
                    self.error_stack.pop()
                    return result
                except ParserError as e:
                    self.add_global_error(
                        f"Error while parsing {strategy.name}: {e}", self.head()
                    )
                    return ErrorNode(self.head().location, self.head())
        # If no strategy could parse the current token, it's an unexpected token
        # Add an error if we aren't inside a strategy already
        # Otherwise, it's up to the strategy to handle the unexpected token
        if not self.error_stack:
            self.add_global_error(
                f"Unexpected token: {self.head().type} ('{self.head().value}')",
                self.head(),
            )
            self.discard()
        else:
            print(
                "Token could not be parsed by any strategy, but already inside a strategy; not adding error."
            )
        return ErrorNode(self.head().location, self.head())

    class NumberParser(ParserStrategy):
        name: str = "Number"

        def can_parse(self) -> bool:
            return self.go(TokenType.NUMBER)

        def parse(self) -> ASTNode:
            token = self.parser.pop()
            return LiteralNode(token.location, token.value, VTypes.NumberType())

    class StringParser(ParserStrategy):
        name: str = "String"

        def can_parse(self) -> bool:
            return self.go(TokenType.STRING)

        def parse(self) -> ASTNode:
            token = self.parser.pop()
            return LiteralNode(token.location, token.value, VTypes.StringType())

    class ListParser(ParserStrategy):
        name: str = "List"

        def can_parse(self) -> bool:
            return self.parser.head_equals(TokenType.LEFT_SQUARE)

        def parse(self) -> ASTNode:
            location = self.parser.head().location
            items = self.parser.parse_items(
                TokenType.LEFT_SQUARE,
                TokenType.COMMA,
                TokenType.RIGHT_SQUARE,
                self.parser.parse_next,
                lambda node: isinstance(node, ErrorNode),
                lambda token: ErrorNode(self.parser.head().location, token),
                singleton=False,
                validate=None,
                multi_item_wrap=lambda items: (
                    items[0] if len(items) == 1 else GroupNode(items[0].location, items)
                ),
            )
            self.parser.eat(TokenType.RIGHT_SQUARE)
            return ListNode(location, items)

    class TupleParser(ParserStrategy):
        name: str = "Tuple"

        def can_parse(self) -> bool:
            return self.parser.head_equals(TokenType.LEFT_PAREN)

        def parse(self) -> ASTNode:
            location = self.parser.head().location
            items = self.parser.parse_items(
                TokenType.LEFT_PAREN,
                TokenType.COMMA,
                TokenType.RIGHT_PAREN,
                self.parser.parse_next,
                lambda node: isinstance(node, ErrorNode),
                lambda token: ErrorNode(self.parser.head().location, token),
                singleton=False,
                validate=None,
                multi_item_wrap=lambda items: (
                    items[0] if len(items) == 1 else GroupNode(items[0].location, items)
                ),
            )
            self.parser.eat(TokenType.RIGHT_PAREN)
            return TupleNode(location, items, len(items))
