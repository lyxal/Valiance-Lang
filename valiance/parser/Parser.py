from abc import abstractmethod
from dataclasses import replace
import itertools
from typing import Callable, Optional, TypeVar
import logging

from valiance.compiler_common import TagCategories
from valiance.loglib.log_block import log_block
from valiance.parser.Errors import EndOfFileTokenError, GenericParseError, ParserError

from valiance.parser.AST import *
from valiance.lexer.Token import Token
from valiance.lexer.TokenType import TokenType
from valiance.vtypes import VTypes
from valiance.compiler_common.Identifier import *

logger = logging.getLogger(__name__)

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

DEFAULT_EAT_NEWLINES_LOCK_STATE = (
    -1,
    True,
)  # By default, consider newlines == whitespace

# A helper function to generate a depth-tracking table for
# token synchronisation.
sync_table = lambda: {_type: 0 for _type in OPEN_CLOSE_TOKEN_MAP}

# A helper function to eother wrap a list of ASTNodes into a GroupNode
# or return the single ASTNode if there's only one.

group_wrap: Callable[[list[ASTNode]], ASTNode]
group_wrap = lambda nodes: (
    nodes[0] if len(nodes) == 1 else GroupNode(nodes[0].location, nodes)
)

# A helper function to either parse an integer or return None
# useful because python doesn't have a parseInt that doesn't
# error


def parseInt(val: str) -> int | None:
    try:
        return int(val)
    except:
        return None


ELEMENT_TOKENS = (
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
    TokenType.EQUALS,
)


class LookaheadPattern:
    pass


class Exactly(LookaheadPattern):
    def __init__(self, token_type: TokenType):
        self.token_type = token_type


class AnyOf(LookaheadPattern):
    def __init__(self, *token_types: TokenType):
        self.token_types = token_types


class Repeated(LookaheadPattern):
    def __init__(
        self,
        pattern: LookaheadPattern,
        min_repeats: int = 0,
        max_repeats: Optional[int] = None,
    ):
        self.pattern = pattern
        self.min_repeats = min_repeats
        self.max_repeats = max_repeats


def is_element_token(token: Token, exclude_underscore: bool = False) -> bool:
    """Determine if a token can be used in an element name

    Args:
        token (Token): The token to check
        exclude_underscore (bool, optional): Whether to exclude underscore as a valid element token. Defaults to False.

    Returns:
        bool: Whether the token can be used in an element name
    """

    if exclude_underscore and token.type == TokenType.UNDERSCORE:
        return False

    return token.type in ELEMENT_TOKENS


def is_expressionable(nodes: list[ASTNode]) -> bool:
    """Determine if a GroupNode or list of ASTNodes can be treated as an expression.

    Args:
        nodes (GroupNode|list[ASTNode]): The nodes to check. Assumed to be not empty.
    Returns:
        bool: Whether the nodes can be treated as an expression
    """
    for node in nodes:

        if isinstance(node, GroupNode):
            for inner_node in node.elements:
                if not is_expressionable([inner_node]):
                    return False
        elif not isinstance(
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
                SafeTypeCastNode,
                UnsafeTypeCastNode,
            ),
        ):
            return False
    return True


class ParserStrategy:
    """A base class for all parser strategies. Do NOT ever create instances of
    this class. Instead, subclass it and implement the abstract methods.

    Takes a Parser instance as an argument to the constructor. Access the parser
    via self.parser.
    """

    name: str = "UnnamedStrategy"

    def __init__(self, parser: Parser):
        self.parser = parser
        self.lock_id = self.parser.gen_new_lock()

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

        # Allow strategies to define whether they should treat
        # newlines as something that should be eaten. Note that
        # if a strategy declares newlines should be eaten, then
        # any calls to substrategies must NOT overwrite that.
        # Hence the need for a lock bound to the strategy's id.
        self.lock_id = 0
        self.eat_newlines = DEFAULT_EAT_NEWLINES_LOCK_STATE  # (lock_id, eat_newlines)

        self._collect_strategies()

    def _collect_strategies(self) -> None:
        # Collect all ParserStrategy subclasses defined in this module
        for subclass in ParserStrategy.__subclasses__():
            self.strategies.append(subclass(self))
        for subclass in self.LabelledStackShuffleParser.__subclasses__():
            self.strategies.append(subclass(self))

    def gen_new_lock(self) -> int:
        """Generate a new id for a strategy. Used solely for determining
        whether eating newlines should be toggled.

        Returns:
            int: The lock id for the parser strategy
        """
        temp = self.lock_id
        self.lock_id += 1
        return temp

    def set_eat_newlines(self, strategy_id: int, to: bool):
        # Allowed to update if id matches OR current id == -1
        if (
            self.eat_newlines[0] == strategy_id
            or self.eat_newlines[0] == DEFAULT_EAT_NEWLINES_LOCK_STATE[0]
        ):
            self.eat_newlines = (strategy_id, to)

    def add_error(self, message: str, location: Token | Location | None) -> None:
        """Add an error to the current error stack

        Args:
            message (str): The error message to display
            location (Token | Location | None): The location of the error. Will default to (-1, -1) [e.g. when EOF is reached]
        """
        if location is not None:
            if isinstance(location, Token):
                self.error_stack[-1].append(
                    GenericParseError(message, location.location)
                )
            else:
                self.error_stack[-1].append(GenericParseError(message, location))
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

    def collect_until(self, *token_types: TokenType) -> list[Token]:
        """Collect tokens until one of the given token types is encountered.

        Args:
            *token_types (TokenType): The token types to stop collecting at.

        Returns:
            list[Token]: The collected tokens.
        """

        collected_tokens: list[Token] = []
        # Initialise the open/close depth tracking table
        open_close_count = sync_table()
        while self.tokens:
            head = self.head(eat_whitespace=False)
            if head.type in token_types and all(
                count == 0 for count in open_close_count.values()
            ):
                # Only stop collecting if we're at depth 0 for all open/close pairs
                break
            if head.type in OPEN_CLOSE_TOKEN_MAP:
                open_close_count[head.type] += 1
            elif head.type in OPEN_CLOSE_TOKEN_MAP.values():
                corresponding_open = [
                    k for k, v in OPEN_CLOSE_TOKEN_MAP.items() if v == head.type
                ][0]
                # Don't worry about unmatched closing tokens here; just collect them
                # The caller can handle any errors about unmatched tokens later
                if open_close_count[corresponding_open] > 0:
                    open_close_count[corresponding_open] -= 1
            collected_tokens.append(self.pop())
        return collected_tokens

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

        while self.head_in(
            TokenType.WHITESPACE,
            TokenType.NEWLINE if self.eat_newlines[1] else TokenType.WHITESPACE,
            eat_whitespace=False,
            care_about_eof=False,
        ):
            self.discard()

    def error_if_eof(
        self, message: Optional[str] = None, eat_whitespace: bool = True
    ) -> None:
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
            eat_whitespace (bool, optional): Whether to consume leading whitespace before checking. Defaults to True. Most of the time, this should be True.

        Raises:
            IndexError: _description_
        """

        if not self.tokens:
            raise EndOfFileTokenError(message or "Unexpected end of input.")
        if eat_whitespace:
            self.eat_whitespace()
        if not self.tokens:
            raise EndOfFileTokenError(message or "Unexpected end of input.")
        if self.tokens[0].type == TokenType.EOF:
            # Delete the EOF token from the stream to prevent infinite loops
            self.discard()
            raise EndOfFileTokenError(message or "Unexpected end of input.")

    def head(self, eat_whitespace: bool = True) -> Token:
        """Get the next token without consuming it.

        Returns:
            Token: The next token in the stream.
        """
        self.error_if_eof(eat_whitespace=eat_whitespace)
        return self.tokens[0]

    def head_equals(
        self,
        token_type: TokenType,
        eat_whitespace: bool = True,
        care_about_eof: bool = True,
    ) -> bool:
        """Check if the next token is of the given type.

        Args:
            token_type (TokenType): The token type to check for
            eat_whitespace (bool, optional): Whether whitespace should be consumed before checking. Defaults to True.
            care_about_eof (bool, optional): Whether to error if EOF is reached while eating whitespace. Defaults to True.

        Returns:
            bool: Whether the next token is of the given type.
        """

        # If no whitespace is to be eaten, don't check for EOF
        # that's because it'll recurse infinitely.

        # Don't eat whitespace if the check is explicitly for whitespace
        # that's a bit silly otherwise.
        eat_whitespace = eat_whitespace and not token_type in (
            TokenType.WHITESPACE,
            TokenType.NEWLINE,
        )
        if eat_whitespace:
            self.eat_whitespace()
            if token_type != TokenType.EOF and care_about_eof:
                self.error_if_eof()
        if not self.tokens:
            return False
        return self.tokens[0].type == token_type

    def head_in(
        self,
        *token_types: TokenType,
        eat_whitespace: bool = True,
        care_about_eof: bool = True,
    ) -> bool:
        """Check if the next token is in the given set of types.

        Args:
            *token_types (TokenType): The token types to check for
            eat_whitespace (bool, optional): Whether whitespace should be consumed before checking. Defaults to True.
            care_about_eof (bool, optional): Whether to error if EOF is reached while eating whitespace. Defaults to True.

        Returns:
            bool: Whether the next token is in the given set of types.
        """
        eat_whitespace = eat_whitespace and not any(
            token_type in (TokenType.WHITESPACE, TokenType.NEWLINE)
            for token_type in token_types
        )

        if eat_whitespace:
            self.eat_whitespace()
            # If explicitly checking for EOF, don't error if EOF is in the set
            if not TokenType.EOF in token_types and care_about_eof:
                self.error_if_eof()
        if not self.tokens:
            return False
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
        self,
        token_types: list[TokenType],
        eat_whitespace: bool = True,
        ignore_whitespace: bool = True,
        care_about_eof: bool = True,
    ) -> bool:
        """Check whether the start of the lookahead matches a given sequence of tokens

        Args:
            token_types (list[TokenType]): The sequence of token types to check for
            eat_whitespace (bool, optional): Whether whitespace should be consumed before checking. Defaults to True.
            ignore_whitespace (bool, optional): Whether whitespace tokens in the lookahead should be ignored. Defaults to True.
            care_about_eof (bool, optional): Whether to error if EOF is reached while eating whitespace. Defaults to True.
        Returns:
            bool: Whether the lookahead matches the given sequence of token types.
        """
        eat_whitespace = eat_whitespace and not any(
            token_type in (TokenType.WHITESPACE, TokenType.NEWLINE)
            for token_type in token_types
        )
        if eat_whitespace:
            self.eat_whitespace()
            if not TokenType.EOF in token_types and care_about_eof:
                self.error_if_eof()

        lookahead_index = 0
        for token_type in token_types:
            # Advance the lookahead index to the next non-whitespace token if ignoring whitespace
            while (
                ignore_whitespace
                and lookahead_index < len(self.tokens)
                and self.tokens[lookahead_index].type == TokenType.WHITESPACE
            ):
                lookahead_index += 1

            if lookahead_index >= len(self.tokens):
                return False

            if self.tokens[lookahead_index].type != token_type:
                return False

            lookahead_index += 1

        return True

    def lookahead_pattern_equals(
        self,
        pattern: list[LookaheadPattern],
        eat_whitespace: bool = True,
        ignore_whitespace: bool = True,
        care_about_eof: bool = True,
    ) -> bool:
        """Check whether the start of the lookahead matches a given pattern of tokens

        Args:
            pattern (list[LookaheadPattern]): The pattern of token types to check for
            eat_whitespace (bool, optional): Whether whitespace should be consumed before checking. Defaults to True.
            ignore_whitespace (bool, optional): Whether whitespace tokens in the lookahead should be ignored. Defaults to True.
            care_about_eof (bool, optional): Whether to error if EOF is reached while eating whitespace. Defaults to True.
        Returns:
            bool: Whether the lookahead matches the given pattern of token types.
        """

        popped_tokens: list[Token] = []
        for pattern_part in pattern:
            if isinstance(pattern_part, Exactly):
                if not self.lookahead_equals(
                    [pattern_part.token_type],
                    eat_whitespace=eat_whitespace,
                    ignore_whitespace=ignore_whitespace,
                    care_about_eof=care_about_eof,
                ):
                    # Restore any popped tokens
                    self.tokens = popped_tokens + self.tokens
                    return False
                popped_tokens.append(self.tokens[0])
                self.discard()
            elif isinstance(pattern_part, AnyOf):
                if not self.lookahead_equals(
                    list(pattern_part.token_types),
                    eat_whitespace=eat_whitespace,
                    ignore_whitespace=ignore_whitespace,
                    care_about_eof=care_about_eof,
                ):
                    # Restore any popped tokens
                    self.tokens = popped_tokens + self.tokens
                    return False
                popped_tokens.append(self.tokens[0])
                self.discard()
            elif isinstance(pattern_part, Repeated):
                count = 0
                while True:
                    if (
                        pattern_part.max_repeats is not None
                        and count >= pattern_part.max_repeats
                    ):
                        break
                    if self.lookahead_pattern_equals(
                        [pattern_part.pattern],
                        eat_whitespace=eat_whitespace,
                        ignore_whitespace=ignore_whitespace,
                        care_about_eof=care_about_eof,
                    ):
                        count += 1
                        popped_tokens.append(self.tokens[0])
                        self.discard()
                    else:
                        break
                if count < pattern_part.min_repeats:
                    # Restore any popped tokens
                    self.tokens = popped_tokens + self.tokens
                    return False

        # Restore any popped tokens
        self.tokens = popped_tokens + self.tokens
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
        self.error_if_eof(eat_whitespace=False)
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
        while self.tokens and not self.head_equals(TokenType.EOF, care_about_eof=False):
            try:
                ast = self.parse_next()
                self.asts.append(ast)
            except ParserError:
                continue
        return self.asts

    def parse_next(self) -> ASTNode:
        """Parse the next item from the token stream.

        Checks the head of the token stream against all defined strategies.

        NOTE: Order of strategy evaluation is not guaranteed, so make
        sure that strategies are mutually exclusive.

        Returns:
            ASTNode: The parsed AST node.
        """

        logger.log(logging.DEBUG, "Parsing next token: %s", self.head())
        logger.log(logging.DEBUG, "Remaining tokens: %s", self.tokens)

        for strategy in self.strategies:
            if strategy.can_parse():

                with log_block(f"Applying strategy: {strategy.name}"):
                    logger.debug(
                        "Strategy %s can parse the current token.", strategy.name
                    )
                    logger.debug("Remaining tokens: %s", self.tokens)

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
                    if self.error_stack[-1]:
                        self.errors.append((strategy.name, self.error_stack[-1]))
                        self.error_stack.pop()
                    else:
                        self.add_global_error(
                            f"Error while parsing {strategy.name}: {e}", self.head_opt()
                        )
                    logger.debug(
                        "Strategy %s raised a ParserError: %s",
                        strategy.name,
                        e,
                    )
                    return ErrorNode(
                        self.head().location if self.head_opt() else Location(-1, -1),
                        self.head_opt() or Token(TokenType.EOF, "", -1, -1),
                    )
            # Clear the strategy's lock on the eat newlines variable if it currently
            # has one
            if self.eat_newlines[0] == strategy.lock_id:
                self.eat_newlines = DEFAULT_EAT_NEWLINES_LOCK_STATE  # Ready for the next strategy to lock
        # If no strategy could parse the current token, it's an unexpected token
        # Add an error if we aren't inside a strategy already
        # Otherwise, it's up to the strategy to handle the unexpected token
        if not self.error_stack:
            self.add_global_error(
                f"Unexpected token: {self.head().type} ('{self.head().value}')",
                self.head(),
            )
        else:
            self.add_error(
                f"Unexpected token: {self.head().type} ('{self.head().value}')",
                self.head(),
            )

        self.discard()
        return ErrorNode(self.head().location, self.head())

    def parse_until(self, *token_types: TokenType) -> list[ASTNode]:
        """Parse tokens until one of the given token types is encountered.

        Args:
            *token_types (TokenType): The token types to stop parsing at.
        Returns:
            list[ASTNode]: The parsed AST nodes.
        """

        with log_block("Parsing until tokens: %s" % (token_types,)):
            logger.debug("Starting parse_until with tokens: %s", self.tokens)
        asts: list[ASTNode] = []
        while not self.head_in(*token_types):
            if not self.tokens:
                break
            ast = self.parse_next()
            asts.append(ast)

        with log_block("Finished parse_until"):
            logger.debug("Finished parse_until with remaining tokens: %s", self.tokens)
        return asts

    def make_type_operation(
        self, left: VTypes.VType, right: VTypes.VType, operator_token: Token
    ) -> VTypes.VType:
        """
        Create a type operation (union or intersection) between two types.

        Args:
            left (VTypes.VType): The left operand type.
            right (VTypes.VType): The right operand type.
            operator_token (Token): The token representing the operator.
        Returns:
            VTypes.VType: The resulting type after applying the operation.
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
                    operator_token,
                )
                return VTypes.ErrorType()

    def parse_identifier(self, *identifier_set: TokenType) -> Identifier:
        """Parse a fully qualified identifier from the token stream.

        Args:
            *identifier_set (TokenType): Additional token types to consider as part of the identifier.

        Returns:
            Identifier: The parsed identifier.
        """

        self.eat_whitespace()
        identifier = self.parse_identifier_fragment(*identifier_set)

        if identifier.name == "":
            self.add_error(
                f"Expected identifier, found {self.head()}", self.head().location
            )
            identifier.error = True

        if self.lookahead_equals([TokenType.DOT], eat_whitespace=False):
            self.eat(TokenType.DOT)
            self.error_if_eof("Expected property after '.' in identifier.")
            property = self.parse_identifier()
            if property.error:
                identifier.error = True
            else:
                identifier.property = property

        return identifier

    def parse_identifier_fragment(self, *identifier_set: TokenType) -> Identifier:
        """Parse only a part of an indentifier. Does not give a fully
        qualified identifier.

        Args:
            *identifier_set (TokenType): Additional token types to consider as part of the identifier.

        Returns:
            Identifier: The parsed identifier fragment.
        """

        self.eat_whitespace()
        identifier = Identifier(self.tokens[0].location)
        while self.head_in(
            *identifier_set,
            TokenType.WORD,
            TokenType.UNDERSCORE,
            care_about_eof=False,
            eat_whitespace=False,
        ):
            identifier.name += self.pop().value

        if identifier.name == "":
            self.add_error(
                f"Expected identifier fragment, found {self.head(eat_whitespace=False)}",
                self.head(eat_whitespace=False).location,
            )
            identifier.error = True

        return identifier

    def parse_index(self) -> StaticIndex:
        index_parts: list[
            ScalarIndex | MDIndex | ScalarVariableIndex | ErrorIndex | None
        ] = []

        self.eat(TokenType.LEFT_SQUARE)

        while not self.head_in(TokenType.COMMA, TokenType.RIGHT_SQUARE):
            # If a colon is encountered, that means that an empty segment
            # has been found. This could be fine (e.g. [::2]) but may
            # also not be fine (e.g. [::] or [:])
            if self.head_equals(TokenType.COLON):
                index_parts.append(None)
            elif self.head_equals(TokenType.NUMBER):
                # Scalar index
                num_token = self.pop()
                if (v := parseInt(num_token.value)) is not None:
                    index_parts.append(ScalarIndex(v))
                else:
                    self.add_error(
                        f"Index must be integer, found {num_token.value}", num_token
                    )
                    index_parts.append(ErrorIndex())
            elif self.head_equals(TokenType.VARIABLE):
                # Scalar index (variable)
                self.discard()  # Discard the VARIABLE token
                ident = self.parse_identifier()
                index_parts.append(ScalarVariableIndex(ident))
            elif self.head_equals(TokenType.LEFT_SQUARE):
                self.discard()
                # Multidimensional index
                coords: list[ScalarIndex | ScalarVariableIndex] = []
                errored = False
                while not self.head_equals(TokenType.RIGHT_SQUARE):
                    if self.head_equals(TokenType.NUMBER):
                        num_token = self.pop()
                        if (v := parseInt(num_token.value)) is not None:
                            coords.append(ScalarIndex(v))
                        else:
                            self.add_error(
                                f"Multi-dimensional index must be integer, found {num_token.value}",
                                num_token,
                            )
                            # This whole MD index is trash, so ignore it and treat it as an error index
                            self.sync(TokenType.RIGHT_SQUARE)
                            index_parts.append(ErrorIndex())
                            errored = True
                            break
                        if not self.head_equals(TokenType.RIGHT_SQUARE):
                            self.eat(TokenType.COMMA)
                    elif self.head_equals(TokenType.VARIABLE):
                        self.discard()  # Discard the VARIABLE token
                        ident = self.parse_identifier()
                        coords.append(ScalarVariableIndex(ident))
                    else:
                        self.add_error(
                            f"Expected number in multi-dimensional index, found {self.head().value}",
                            self.head(),
                        )
                        index_parts.append(ErrorIndex())
                        self.sync(TokenType.RIGHT_SQUARE)
                        errored = True
                        break
                if not errored:
                    index_parts.append(MDIndex(coords))
                self.eat(TokenType.RIGHT_SQUARE)
            else:
                self.add_error(
                    f"Expected scalar index, slice, or multi-dimension index, found {self.head()}",
                    self.head(),
                )
                self.sync(TokenType.COMMA, TokenType.RIGHT_SQUARE)

            # Eat an optional COLON after the item
            if self.head_equals(TokenType.COLON):
                self.discard()

            if not self.head_in(TokenType.COMMA, TokenType.RIGHT_SQUARE):
                self.add_error(
                    f"Expected comma or right square bracket in index, found {self.head()}",
                    self.head(),
                )
                self.sync(TokenType.COMMA, TokenType.RIGHT_SQUARE)

            if self.head_equals(TokenType.COMMA):
                self.discard()

        self.eat(TokenType.RIGHT_SQUARE)

        if len(index_parts) == 3:
            return SliceIndex(index_parts[0], index_parts[1], index_parts[2])
        elif len(index_parts) == 2:
            return SliceIndex(index_parts[0], index_parts[1], None)
        elif len(index_parts) == 1:
            assert index_parts[0] is not None
            return index_parts[0]
        else:
            return ErrorIndex()

    def parse_type(self, min_precedence: int = 0) -> VType:
        """Parse a type from the token stream.

        NOTE: Normal usage should not need to specify min_precedence.
        It's an internal detail used for parsing type expressions with
        operator precedence.

        Args:
            min_precedence (int, optional): The minimum precedence level for parsing. Defaults to 0.

        Returns:
            VType: The parsed type.
        """

        left = self.parse_primary_type()

        if self.tokens[0].type == TokenType.EOF:
            return left

        postfix_modifiers: list[Token] = []

        if self.lookahead_equals(
            [TokenType.PLUS, TokenType.VARIABLE], care_about_eof=False
        ):
            self.eat(TokenType.PLUS)
            var_token = self.pop()
            left = VTypes.ExactRankType(left, var_token.value)
        else:
            while self.head_in(
                TokenType.PLUS,
                TokenType.STAR,
                TokenType.TILDE,
                TokenType.QUESTION,
                TokenType.NUMBER,
                TokenType.EXCLAMATION,
                care_about_eof=False,
            ):
                if self.head_equals(TokenType.NUMBER):
                    number = self.pop()
                    if not postfix_modifiers:
                        self.add_error(
                            "Rank modifier number must be preceded by a rank modifier operator (+, *, ~, ?).",
                            number,
                        )
                        return VTypes.ErrorType()
                    try:
                        rank = int(number.value)
                        modifier = postfix_modifiers.pop()
                        postfix_modifiers.extend([modifier] * rank)
                    except ValueError:
                        self.add_error(
                            f"Invalid rank modifier number: '{number.value}' is not a valid integer.",
                            number,
                        )
                        return VTypes.ErrorType()
                else:
                    modifier_token = self.pop()
                    postfix_modifiers.append(modifier_token)
            grouped_modifiers = itertools.groupby(
                postfix_modifiers, key=lambda t: t.type
            )
            for modifier_token, group in grouped_modifiers:
                group = list(group)
                count = len(group)
                match modifier_token:
                    case TokenType.PLUS:
                        left = VTypes.ExactRankType(left, count)
                    case TokenType.STAR:
                        left = VTypes.MinimumRankType(left, count)
                    case TokenType.TILDE:
                        left = VTypes.ListType(left, count)
                    case TokenType.QUESTION:
                        for _ in range(count):
                            left = VTypes.OptionalType(left)
                    case TokenType.EXCLAMATION:
                        if count > 1:
                            self.add_error(
                                "Non-vectorising modifier '!' can only be applied once.",
                                group[0],
                            )
                            left = VTypes.ErrorType()
                            break
                        left.non_vectorising = True
                    case _:
                        raise RuntimeError("Unreachable code reached.")

        while (
            self.head().value in TYPE_OPERATOR_PRECEDENCE_TABLE
            and TYPE_OPERATOR_PRECEDENCE_TABLE[self.head().value] >= min_precedence
        ):
            operator_token = self.pop()
            operator = operator_token.value
            precedence = TYPE_OPERATOR_PRECEDENCE_TABLE[operator]
            if precedence < min_precedence:
                break
            right = self.parse_type(precedence + 1)
            left = self.make_type_operation(left, right, operator_token)

        return left

    def parse_primary_type(self) -> VType:
        """Parse a primary type from the token stream.

        Primary types are basic types like identifiers, literals, lists, tuples, etc.

        NOTE: This method is called by parse_type to handle the base cases.
        Do not call this method directly unless you know what you're doing.

        Returns:
            VType: The parsed primary type.
        """

        data_tags: list[VTypes.DataTag] = []

        self.eat_whitespace()

        # First, handle data tags
        while self.head_equals(TokenType.HASH):
            self.discard()  # Discard the tag token
            tag_name = self.parse_identifier()
            depth = 0
            if self.lookahead_equals([TokenType.PLUS, TokenType.NUMBER]):
                self.pop()  # Pop the plus
                number_token = self.pop()
                try:
                    depth = int(number_token.value)
                except ValueError:
                    self.add_error(
                        f"Invalid data tag depth: '{number_token.value}' is not a valid integer.",
                        number_token,
                    )
            else:
                while self.head_equals(TokenType.PLUS):
                    self.pop()
                    depth += 1
            data_tags.append(VTypes.DataTag(name=tag_name, depth=depth))

        # Then, handle grouping
        if self.head_equals(TokenType.LEFT_BRACE):
            self.eat(TokenType.LEFT_BRACE)
            inner_type = self.parse_type()
            self.eat(TokenType.RIGHT_BRACE)
            return replace(inner_type, data_tags=tuple(data_tags))

        if self.head_equals(TokenType.WORD):
            type_name = self.parse_identifier()
            left_type_args: list[VTypes.VType] = []
            right_type_args: list[VTypes.VType] = []

            # Parse type arguments if present
            if self.head_equals(TokenType.LEFT_SQUARE, care_about_eof=False):
                self.eat(TokenType.LEFT_SQUARE)
                # Parse left type arguments
                while not self.head_equals(TokenType.COLON) and not self.head_equals(
                    TokenType.RIGHT_SQUARE
                ):
                    left_type_args.append(self.parse_type())
                    if self.head_equals(TokenType.COMMA):
                        self.eat(TokenType.COMMA)
                    else:
                        break
                # If there's a colon, parse right type arguments
                if self.head_equals(TokenType.ARROW):
                    self.eat(TokenType.ARROW)
                    while not self.head_equals(TokenType.RIGHT_SQUARE):
                        right_type_args.append(self.parse_type())
                        if self.head_equals(TokenType.COMMA):
                            self.eat(TokenType.COMMA)
                        else:
                            break
                self.eat(TokenType.RIGHT_SQUARE)

            element_tags: list[VTypes.ElementTag] = []
            negate_next = False
            if self.head_equals(TokenType.COLON, care_about_eof=False):
                self.pop()  # Pop the colon
                if self.head_equals(TokenType.MINUS):
                    self.pop()  # Pop the MINUS
                    negate_next = True
                while self.head_equals(TokenType.WORD):
                    tag_name = self.parse_identifier()
                    if negate_next:
                        element_tags.append(VTypes.NegateElementTag(name=tag_name))
                    else:
                        element_tags.append(VTypes.ElementTag(name=tag_name))
                    if self.head_equals(TokenType.PLUS):
                        self.pop()  # Pop the PLUS
                        negate_next = False
                    else:
                        break
            return VTypes.type_name_to_vtype(
                type_name, (left_type_args, right_type_args), data_tags, element_tags
            )
        else:
            self.add_error(
                f"Expected a primary type, got {self.head().type} ('{self.head().value}')",
                self.head(),
            )
            return VTypes.ErrorType()

    def parse_parameter_list(self, skip_left_paren: bool = False) -> list[Parameter]:
        """Parse a list of parameters to a `fn` or a `define`

        Note: Does NOT account for constructor syntax.

        Returns:
            list[Tuple[str, VTypes.VType]]: The parsed parameters as a list of (name, type) tuples.
        """

        parameters: list[Parameter] = []

        if not skip_left_paren:
            self.eat(TokenType.LEFT_PAREN)

        if self.head_equals(TokenType.RIGHT_PAREN):
            return parameters

        # Track the number of anonymous generics in this parameter list
        anonymous_generic_id = 0

        while not self.head_equals(TokenType.RIGHT_PAREN):
            # Get the name and type of the parameter
            # Note that name may be empty

            parameter_name = self.parse_identifier_fragment()
            parameter_type: VType
            if self.head_equals(TokenType.COLON):
                self.discard()
                parameter_type = self.parse_type()
            else:
                parameter_type = VTypes.AnonymousGeneric(anonymous_generic_id)
                anonymous_generic_id += 1

            # Now, collect any cast options
            cast_type: VType | None = None
            if self.head_equals(TokenType.AS):
                self.discard()
                cast_type = self.parse_type()

            # Finally, collect the default value if present.
            default_value: ASTNode | None = None
            if self.head_equals(TokenType.EQUALS):
                eq_tok_location = self.pop()
                nodes = self.parse_until(TokenType.COMMA, TokenType.RIGHT_PAREN)
                if not is_expressionable(nodes):
                    self.add_error(
                        "Default value of parameter must be expressionable",
                        eq_tok_location,
                    )
                default_value = group_wrap(nodes)

            parameters.append(
                Parameter(parameter_name, parameter_type, cast_type, default_value)
            )

            if not self.head_equals(TokenType.RIGHT_PAREN):
                if not self.eat(
                    TokenType.COMMA,
                    "Expected ',' between parameters.",
                ):
                    self.sync(TokenType.COMMA, TokenType.RIGHT_PAREN)

        return parameters

    def parse_block(self) -> ASTNode:
        """Parse a block of statements enclosed in curly braces.

        Returns:
            ASTNode: The parsed block.
        """

        location_token = self.head()
        if not self.eat(TokenType.LEFT_BRACE):
            self.sync(TokenType.RIGHT_BRACE)
            return ErrorNode(location_token.location, location_token)

        items = self.parse_until(TokenType.RIGHT_BRACE)
        self.eat(TokenType.RIGHT_BRACE)
        return GroupNode(location_token.location, items)

    def parse_parameter_condition_split(
        self,
    ) -> tuple[Optional[list[Parameter]], ASTNode]:
        """Parse the condition, and optionally parameters of a struture like
        while or unfold.

        Assumes that the left parenthesis has been left on the token stream

        Returns:
            tuple[Optional[ASTNode], ASTNode]: Parameters (if present) and condition
        """

        # Step one is to get to just after the right paren

        self.eat(TokenType.LEFT_PAREN)
        first_part = self.collect_until(TokenType.RIGHT_PAREN)

        right_paren = self.head()
        if not self.eat(TokenType.RIGHT_PAREN):
            self.sync(TokenType.RIGHT_PAREN)
            return (None, ErrorNode(right_paren.location, right_paren))

        # Step two is to determine what kind of situation we're
        # facing. If there's an arrow, it's parameters and condition
        # otherwise it's just condition

        head_is_arrow = self.head_equals(TokenType.ARROW)

        # Step three is to push all tokens back onto the token stream
        # ready for parsing. The right paren also needs to be pushed back
        # so that there's a stop point.

        self.tokens = first_part + [right_paren] + self.tokens

        # Step four is normal parsing
        if head_is_arrow:
            parameters = self.parse_parameter_list(skip_left_paren=True)
            self.eat(TokenType.RIGHT_PAREN)
            self.eat(TokenType.ARROW)
            self.eat(TokenType.LEFT_PAREN)
        else:
            parameters = None

        condition = self.parse_until(TokenType.RIGHT_PAREN)

        self.eat(TokenType.RIGHT_PAREN)

        return (parameters, group_wrap(condition))

    def parse_generics(self) -> list[VType]:
        return self.parse_items(
            TokenType.LEFT_SQUARE,
            TokenType.COMMA,
            TokenType.RIGHT_SQUARE,
            lambda: VTypes.type_name_to_vtype(
                self.parse_identifier(), ([], []), [], []
            ),
            lambda t: isinstance(t, VTypes.ErrorType),
            lambda _: VTypes.ErrorType(),
            singleton=True,
            validate=None,
        )

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
            return self.go(TokenType.LEFT_SQUARE)

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
                validate=lambda node: is_expressionable([node]),
                multi_item_wrap=lambda items: (
                    items[0] if len(items) == 1 else GroupNode(items[0].location, items)
                ),
            )
            self.parser.eat(TokenType.RIGHT_SQUARE)
            return ListNode(location, items)

    class TupleParser(ParserStrategy):
        name: str = "Tuple"

        def can_parse(self) -> bool:
            return self.go(TokenType.LEFT_PAREN)

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
                validate=lambda node: is_expressionable([node]),
                multi_item_wrap=lambda items: (
                    items[0] if len(items) == 1 else GroupNode(items[0].location, items)
                ),
            )
            self.parser.eat(TokenType.RIGHT_PAREN)
            return TupleNode(location, items, len(items))

    class BlockParser(ParserStrategy):
        name: str = "Block"

        def can_parse(self) -> bool:
            return self.go(TokenType.LEFT_BRACE)

        def parse(self) -> ASTNode:
            return self.parser.parse_block()

    class ElementParser(ParserStrategy):
        name: str = "Element"

        def can_parse(self) -> bool:
            return is_element_token(self.parser.head(), exclude_underscore=True)

        def parse(self) -> ASTNode:
            location_token = self.parser.head()

            name = self.parser.parse_identifier(*ELEMENT_TOKENS)

            if name.name == "=":
                self.parser.add_error(
                    "Element name cannot be '='.", location_token.location
                )
                return ErrorNode(location_token.location, location_token)

            # Handle potential type arguments for the element
            args: list[VTypes.VType] = []
            if self.parser.head_equals(TokenType.LEFT_SQUARE, care_about_eof=False):
                args = self.parser.parse_items(
                    TokenType.LEFT_SQUARE,
                    TokenType.COMMA,
                    TokenType.RIGHT_SQUARE,
                    self.parser.parse_type,
                    lambda t: isinstance(t, VTypes.ErrorType),
                    lambda token: VTypes.ErrorType(),
                    singleton=True,
                    validate=None,
                )
                self.parser.eat(TokenType.RIGHT_SQUARE)

            # Collect any arguments for the element
            arg_nodes: list[Tuple[Identifier, ASTNode]] = []
            if self.parser.head_equals(TokenType.LEFT_PAREN, care_about_eof=False):
                arg_nodes = self.parse_element_arguments()

            modifier_args: list[ASTNode] = []
            # And finally, check for the presence of modifier arguments
            if self.parser.head_equals(
                TokenType.COLON, care_about_eof=False, eat_whitespace=False
            ):
                colon_token = self.parser.pop()  # Pop the colon
                # We start caring about EOF now because a modifier requires
                # more.
                if self.parser.head_equals(TokenType.LEFT_PAREN):
                    modifier_args = self.parser.parse_items(
                        TokenType.LEFT_PAREN,
                        TokenType.COMMA,
                        TokenType.RIGHT_PAREN,
                        self.parser.parse_next,
                        lambda node: isinstance(node, ErrorNode),
                        lambda token: ErrorNode(self.parser.head().location, token),
                        singleton=False,
                        validate=lambda node: is_expressionable([node]),
                        multi_item_wrap=lambda items: (
                            items[0]
                            if len(items) == 1
                            else GroupNode(items[0].location, items)
                        ),
                    )
                    self.parser.eat(TokenType.RIGHT_PAREN)
                else:
                    modified_arg = self.parser.parse_next()
                    if not is_expressionable([modified_arg]):
                        self.parser.add_error(
                            "Modifier argument must be expressionable.",
                            modified_arg.location,
                        )
                        modified_arg = ErrorNode(colon_token.location, colon_token)
                    modifier_args = [modified_arg]

            return ElementNode(
                location=location_token.location,
                element_name=name,
                generics=args,
                args=arg_nodes,
                modifier_args=modifier_args,
            )

        def parse_element_arguments(self) -> list[Tuple[Identifier, ASTNode]]:
            """Parse the arguments for an element.

            Returns:
                list[Tuple[Identifier, ASTNode]]: The parsed arguments as a list of (name, ASTNode) tuples.
            """
            arguments: list[Tuple[Identifier, ASTNode]] = []

            self.parser.pop()

            while not self.parser.head_equals(TokenType.RIGHT_PAREN):
                logger.log(
                    logging.DEBUG,
                    "Parsing element argument, head token: %s",
                    self.parser.head(),
                )
                name = Identifier(location=self.parser.tokens[0].location)
                args: list[ASTNode] = []
                if self.parser.lookahead_pattern_equals(
                    [
                        Exactly(TokenType.WORD),
                        Repeated(AnyOf(TokenType.WORD, TokenType.UNDERSCORE)),
                        Exactly(TokenType.EQUALS),
                    ]
                ):
                    name = self.parser.parse_identifier()
                    self.parser.eat(TokenType.EQUALS)  # Pop the EQUALS token

                # From here, the argument will either be `_` (fill when called), `#` (fill now), or an series of expressionable ASTs
                if self.parser.head_equals(TokenType.UNDERSCORE):
                    args = [ElementArgumentIgnoreNode(self.parser.pop().location)]
                elif self.parser.head_equals(TokenType.HASH):
                    args = [ElementArgumentFillNode(self.parser.pop().location)]
                else:
                    args = self.parser.parse_until(
                        TokenType.COMMA, TokenType.RIGHT_PAREN
                    )
                    logger.log(logging.DEBUG, "Parsed element argument ASTs: %s", args)
                    logger.log(
                        logging.DEBUG, "Remaining tokens: %s", self.parser.tokens
                    )
                    if not args:
                        self.parser.add_error(
                            "Expected at least one argument for element argument.",
                            self.parser.head(),
                        )
                        return []

                    if not is_expressionable(args):
                        self.parser.add_error(
                            "Element argument contains non-expressionable AST nodes.",
                            self.parser.head(),
                        )
                        return []

                arguments.append((name, group_wrap(args)))
                if self.parser.head_equals(TokenType.COMMA):
                    self.parser.eat(TokenType.COMMA)

            self.parser.eat(TokenType.RIGHT_PAREN)
            with log_block("Finished parsing element arguments"):
                logger.debug("Parsed element arguments: %s", arguments)
                logger.debug("Remaining tokens: %s", self.parser.tokens)
            return arguments

    class LabelledStackShuffleParser(ParserStrategy):
        name: str = "AbstractStackShuffle"
        nice_name: str = "StackShuffle"  # Replace with duplicate/swap/pop, etc
        AST_type: type[ASTNode]

        def can_parse(self) -> bool:
            # Never use this strategy directly
            return False

        def parse(self) -> ASTNode:
            shuffle_token = self.parser.pop()  # Pop the shuffle type token

            # Account for the fact that it may be a default shuffle.
            if not self.parser.head_equals(TokenType.LEFT_SQUARE):
                return self.build_node(shuffle_token, [], [])
            self.parser.eat(TokenType.LEFT_SQUARE)

            # Collect all pre-stack labels
            pre_stack: list[str] = []

            while True:
                if self.parser.head_in(TokenType.WORD, TokenType.UNDERSCORE):
                    pre_stack.append(self.parser.pop().value)
                else:
                    self.parser.add_error(
                        f"Expected a label (WORD or UNDERSCORE) in pre-stack of {self.nice_name}. Found {self.parser.head().type}.",
                        self.parser.head(),
                    )
                    self.parser.sync(TokenType.ARROW, TokenType.RIGHT_SQUARE)
                    break

                if self.parser.head_equals(TokenType.COMMA):
                    self.parser.eat(TokenType.COMMA)
                elif self.parser.head_in(TokenType.ARROW, TokenType.RIGHT_SQUARE):
                    break
                else:
                    self.parser.add_error(
                        f"Expected ',' or '->' or ']' in pre-stack of {self.nice_name}. Found {self.parser.head().type}.",
                        self.parser.head(),
                    )
                    self.parser.sync(TokenType.ARROW, TokenType.RIGHT_SQUARE)
                    break

            # Collect all post-stack labels
            # Note that it is up to the specific shuffle type to enforce
            # whether a post-stack is required.
            post_stack: list[str] = []

            if self.parser.head_equals(TokenType.ARROW):
                self.parser.eat(TokenType.ARROW)

                while True:
                    if self.parser.head_in(TokenType.WORD, TokenType.UNDERSCORE):
                        post_stack.append(self.parser.pop().value)
                    else:
                        self.parser.add_error(
                            f"Expected a label (WORD or UNDERSCORE) in post-stack of {self.nice_name}. Found {self.parser.head().type}.",
                            self.parser.head(),
                        )
                        self.parser.sync(TokenType.RIGHT_SQUARE)
                        break

                    if self.parser.head_equals(TokenType.COMMA):
                        self.parser.eat(TokenType.COMMA)
                    elif self.parser.head_equals(TokenType.RIGHT_SQUARE):
                        break
                    else:
                        self.parser.add_error(
                            f"Expected ',' or ']' in post-stack of {self.nice_name}. Found {self.parser.head().type}.",
                            self.parser.head(),
                        )
                        self.parser.sync(TokenType.RIGHT_SQUARE)
                        break

            self.parser.eat(TokenType.RIGHT_SQUARE)

            return self.build_node(shuffle_token, pre_stack, post_stack)

        @abstractmethod
        def build_node(
            self, shuffle_token: Token, pre_stack: list[str], post_stack: list[str]
        ) -> ASTNode:
            pass

    class DuplicateParser(LabelledStackShuffleParser):
        name: str = "Duplicate"
        nice_name: str = "Duplicate"
        AST_type: type[ASTNode] = DuplicateNode

        def can_parse(self) -> bool:
            return self.go(TokenType.DUPLICATE)

        def build_node(
            self, shuffle_token: Token, pre_stack: list[str], post_stack: list[str]
        ) -> ASTNode:
            return DuplicateNode(shuffle_token.location, pre_stack, post_stack)

    class SwapParser(LabelledStackShuffleParser):
        name: str = "Swap"
        nice_name: str = "Swap"
        AST_type: type[ASTNode] = SwapNode

        def can_parse(self) -> bool:
            return self.go(TokenType.SWAP)

        def build_node(
            self, shuffle_token: Token, pre_stack: list[str], post_stack: list[str]
        ) -> ASTNode:
            return SwapNode(shuffle_token.location, pre_stack, post_stack)

    class PopParser(LabelledStackShuffleParser):
        name: str = "Pop"
        nice_name: str = "Pop"
        AST_type: type[ASTNode] = PopNode

        def can_parse(self) -> bool:
            return self.go(TokenType.UNDERSCORE)

        def build_node(
            self, shuffle_token: Token, pre_stack: list[str], post_stack: list[str]
        ) -> ASTNode:
            if post_stack:
                self.parser.add_error(
                    "Pop operation cannot have a post-stack.",
                    shuffle_token,
                )
                return ErrorNode(shuffle_token.location, shuffle_token)
            return PopNode(shuffle_token.location, pre_stack, [])

    class FunctionParser(ParserStrategy):
        name: str = "Function"

        def can_parse(self) -> bool:
            return self.go(TokenType.FN)

        def parse(self) -> ASTNode:
            location_token = self.parser.pop()  # Pop the 'fn' token
            generics: list[VTypes.VType] = []

            if self.parser.head_equals(TokenType.LEFT_SQUARE):
                generics = self.parser.parse_generics()
                self.parser.eat(TokenType.RIGHT_SQUARE)

            parameters: list[Parameter] = []
            if self.parser.head_equals(TokenType.LEFT_PAREN):
                parameters = self.parser.parse_parameter_list()

                if not self.parser.eat(TokenType.RIGHT_PAREN):
                    self.parser.sync(TokenType.ARROW, TokenType.LEFT_BRACE)

            element_tags: list[VTypes.ElementTag] = []
            if self.parser.head_equals(TokenType.COLON):
                self.parser.pop()  # Pop the colon
                negate_next = False
                if self.parser.head_equals(TokenType.MINUS):
                    self.parser.pop()  # Pop the MINUS
                    negate_next = True
                while self.parser.head_equals(TokenType.WORD):

                    tag_name = self.parser.parse_identifier()
                    if negate_next:
                        element_tags.append(VTypes.NegateElementTag(name=tag_name))
                    else:
                        element_tags.append(VTypes.ElementTag(name=tag_name))

                    if self.parser.head_equals(TokenType.PLUS):
                        self.parser.pop()  # Pop the PLUS
                        negate_next = False
                    else:
                        break

            output_types: list[VTypes.VType] = []
            if self.parser.head_equals(TokenType.ARROW):
                self.parser.eat(TokenType.ARROW)
                while not self.parser.head_equals(TokenType.LEFT_BRACE):
                    output_type = self.parser.parse_type()
                    output_types.append(output_type)
                    if self.parser.head_equals(TokenType.COMMA):
                        self.parser.eat(TokenType.COMMA)
                    else:
                        break
            body = self.parser.parse_block()

            return FunctionNode(
                location_token.location,
                generics,
                parameters,
                output_types,
                body,
                tuple(element_tags),
            )

    class VariableParser(ParserStrategy):
        name: str = "Variable"

        def can_parse(self) -> bool:
            return self.go(TokenType.VARIABLE)

        def parse(self) -> ASTNode:
            variable_token = self.parser.pop()

            name_components: list[Identifier] = [
                Identifier(self.parser.tokens[0].location)
            ]

            while self.parser.head_in(
                TokenType.WORD,
                TokenType.UNDERSCORE,
                TokenType.LEFT_SQUARE,
                TokenType.DOT,
                care_about_eof=False,
                eat_whitespace=False,
            ):
                if self.parser.head_in(
                    TokenType.WORD,
                    TokenType.UNDERSCORE,
                    care_about_eof=False,
                    eat_whitespace=False,
                ):
                    name_components[-1] = self.parser.parse_identifier()
                elif self.parser.lookahead_equals(
                    [TokenType.DOT], eat_whitespace=False
                ):
                    self.parser.eat(TokenType.DOT)
                    if not self.parser.head_in(TokenType.WORD, TokenType.UNDERSCORE):
                        self.parser.add_error(
                            f"Expected identifier after dot, found {self.parser.head()}",
                            self.parser.head(),
                        )
                        break
                    name_components.append(Identifier(self.parser.tokens[0].location))
                else:
                    name_components[-1].index = self.parser.parse_index()
                    if not self.parser.head_equals(TokenType.DOT, care_about_eof=False):
                        break

            variable_name: Identifier = name_components.pop()
            for component in reversed(name_components):
                variable_name = Identifier(
                    location=component.location,
                    name=component.name,
                    index=component.index,
                    property=variable_name,
                )

            if self.parser.head_equals(TokenType.COLON, care_about_eof=False):
                # Augmented variable assignment
                self.parser.eat(TokenType.COLON)  # Pop the COLON token
                function = self.parser.parse_next()
                return AugmentedVariableSetNode(
                    variable_token.location,
                    variable_name,
                    function,
                )
            if not self.parser.head_equals(TokenType.EQUALS, care_about_eof=False):
                # No assignment, just a variable get
                return VariableGetNode(
                    variable_token.location,
                    variable_name,
                )
            # Variable assignment
            self.parser.eat(TokenType.EQUALS)  # Pop the EQUALS token
            self.parser.set_eat_newlines(self.lock_id, False)
            values = self.parser.parse_until(
                TokenType.SEMICOLON,
                TokenType.NEWLINE,
                TokenType.EOF,
                TokenType.RIGHT_PAREN,
                TokenType.RIGHT_SQUARE,
                TokenType.RIGHT_BRACE,
            )
            if not values:
                self.parser.add_error(
                    "Variable assignment must have at least one value.",
                    variable_token,
                )
                return ErrorNode(variable_token.location, variable_token)
            if not is_expressionable(values):
                first_bad_ast = [ast for ast in values if not is_expressionable([ast])][
                    0
                ]
                self.parser.add_error(
                    f"Variable assignment contains non-expressionable AST node of type {type(first_bad_ast).__name__}.",
                    first_bad_ast.location,
                )
                return ErrorNode(variable_token.location, variable_token)
            if self.parser.head_in(
                TokenType.SEMICOLON, TokenType.NEWLINE, TokenType.EOF
            ):
                self.parser.discard()  # Pop the SEMICOLON or NEWLINE
            value_node = group_wrap(values)
            return VariableSetNode(
                variable_token.location,
                variable_name,
                value_node,
            )

    class MultiVariableParser(ParserStrategy):
        name: str = "Multi-Variable Assignment"

        def can_parse(self) -> bool:
            return self.go(TokenType.MULTI_VARIABLE)

        def parse(self) -> ASTNode:
            multi_variable_token = self.parser.pop()  # Pop the MULTI_VARIABLE token
            names: list[Identifier] = []

            while True:
                if self.parser.head_in(TokenType.WORD, TokenType.UNDERSCORE):
                    names.append(self.parser.parse_identifier())
                else:
                    self.parser.add_error(
                        f"Expected variable name (WORD or UNDERSCORE) in multi-variable assignment. Found {self.parser.head().type}.",
                        self.parser.head(),
                    )
                    self.parser.sync(TokenType.COMMA, TokenType.RIGHT_PAREN)
                    break
                if self.parser.head_equals(TokenType.COMMA):
                    self.parser.pop()
                elif self.parser.head_equals(TokenType.RIGHT_PAREN):
                    break
                else:
                    self.parser.add_error(
                        f"Expected ',' or ')' in multi-variable assignment. Found {self.parser.head().type}.",
                        self.parser.head(),
                    )
                    self.parser.sync(TokenType.COMMA, TokenType.RIGHT_PAREN)
                    break

            self.parser.eat(TokenType.RIGHT_PAREN)
            if not names:
                self.parser.add_error(
                    "Multi-variable assignment must have at least one variable name.",
                    multi_variable_token,
                )
                return ErrorNode(multi_variable_token.location, multi_variable_token)

            if not self.parser.eat(TokenType.EQUALS):  # Pop the EQUALS token
                return ErrorNode(multi_variable_token.location, multi_variable_token)
            self.parser.set_eat_newlines(self.lock_id, False)
            values: list[ASTNode] = self.parser.parse_until(
                TokenType.SEMICOLON, TokenType.NEWLINE, TokenType.EOF
            )

            if not values:
                self.parser.add_error(
                    "Multi-variable assignment must have at least one value.",
                    multi_variable_token,
                )
                return ErrorNode(multi_variable_token.location, multi_variable_token)
            if not is_expressionable(values):
                first_bad_ast = [ast for ast in values if not is_expressionable([ast])][
                    0
                ]
                self.parser.add_error(
                    f"Multi-variable assignment contains non-expressionable AST node of type {type(first_bad_ast).__name__}.",
                    first_bad_ast.location,
                )
                return ErrorNode(multi_variable_token.location, multi_variable_token)
            if self.parser.head_in(
                TokenType.SEMICOLON, TokenType.NEWLINE, TokenType.EOF
            ):
                self.parser.discard()  # Pop the SEMICOLON or NEWLINE

            value_node = group_wrap(values)
            return MultipleVariableSetNode(
                multi_variable_token.location,
                names,
                value_node,
            )

    class SkipTokenParser(ParserStrategy):
        def can_parse(self) -> bool:
            return (
                self.go(TokenType.PASS)
                or self.go(TokenType.SEMICOLON)
                or self.go(TokenType.NEWLINE)
            )

        def parse(self) -> ASTNode:
            return AuxiliaryNode(self.parser.pop().location)

    class IfParser(ParserStrategy):
        name: str = "If Statement"

        def can_parse(self):
            return self.go(TokenType.IF)

        def parse(self):
            with log_block("If Statement Parsing"):
                logging.debug(
                    "Parsing IF statement, head token: %s", self.parser.head()
                )
                logging.debug("Remaining tokens: %s", self.parser.tokens)

            location_token = self.parser.pop()
            condition: ASTNode
            if self.parser.eat(TokenType.LEFT_PAREN):
                condition = group_wrap(self.parser.parse_until(TokenType.RIGHT_PAREN))
                self.parser.eat(TokenType.RIGHT_PAREN)
            else:
                bad_token = self.parser.head()
                self.parser.sync(TokenType.RIGHT_PAREN)
                condition = ErrorNode(bad_token.location, bad_token)

            with log_block("The If Statement Condition"):
                logging.debug("Parsed IF condition AST: %s", condition)
                logging.debug("Remaining tokens: %s", self.parser.tokens)

            if_block = self.parser.parse_block()

            with log_block("The If Statement Body"):
                logging.debug("Parsed IF body AST: %s", if_block)
                logging.debug("Remaining tokens: %s", self.parser.tokens)

            else_block: ASTNode | None = None
            if self.parser.head_equals(TokenType.ELSE, care_about_eof=False):
                self.parser.discard()
                if self.parser.head_equals(TokenType.IF):
                    else_block = self.parse()
                else:
                    else_block = self.parser.parse_block()

            return IfNode(location_token.location, condition, if_block, else_block)

    class WhileParser(ParserStrategy):
        name: str = "While Loop"

        def can_parse(self) -> bool:
            return self.go(TokenType.WHILE)

        def parse(self) -> ASTNode:
            location_token = self.parser.pop()  # Pop the 'while' token
            parameters: list[Parameter] | None
            condition: ASTNode

            (parameters, condition) = self.parser.parse_parameter_condition_split()
            body = self.parser.parse_block()

            return WhileNode(
                location_token.location,
                parameters,
                condition,
                body,
            )

    class UnfoldParser(ParserStrategy):
        name: str = "Unfold Operation"

        def can_parse(self) -> bool:
            return self.go(TokenType.UNFOLD)

        def parse(self) -> ASTNode:
            location_token = self.parser.pop()  # Pop the 'unfold' token
            parameters: list[Parameter] | None
            condition: ASTNode

            (parameters, condition) = self.parser.parse_parameter_condition_split()
            body = self.parser.parse_block()

            return UnfoldNode(
                location_token.location,
                parameters,
                condition,
                body,
            )

    class ForEachParser(ParserStrategy):
        name: str = "For Loop"

        def can_parse(self) -> bool:
            return self.go(TokenType.FOREACH)

        def parse(self) -> ASTNode:
            location_token = self.parser.pop()  # Pop the 'for' token
            self.parser.eat(TokenType.LEFT_PAREN)
            iterator = self.parser.parse_identifier()
            index: Identifier | None = None
            if self.parser.head_equals(TokenType.COMMA):
                self.parser.discard()
                index = self.parser.parse_identifier_fragment()
            self.parser.eat(TokenType.RIGHT_PAREN)
            body = self.parser.parse_block()
            return ForNode(
                location_token.location,
                iterator,
                index,
                body,
            )

    class DefineParser(ParserStrategy):
        name: str = "Define Statement"

        def can_parse(self) -> bool:
            return self.go(TokenType.DEFINE)

        def parse(self) -> ASTNode:
            location_token = self.parser.pop()  # Pop the 'define' token

            generics: list[VTypes.VType] = []

            if self.parser.head_equals(TokenType.LEFT_SQUARE):
                generics = self.parser.parse_generics()
                self.parser.eat(TokenType.RIGHT_SQUARE)

            name = self.parser.parse_identifier()
            parameters: list[Parameter] = []
            if self.parser.head_equals(TokenType.LEFT_PAREN):
                parameters = self.parser.parse_parameter_list()

                if not self.parser.eat(TokenType.RIGHT_PAREN):
                    self.parser.sync(TokenType.EQUALS, TokenType.LEFT_BRACE)

            element_tags: list[VTypes.ElementTag] = []
            if self.parser.head_equals(TokenType.COLON):
                self.parser.pop()
                while self.parser.head_equals(TokenType.WORD):
                    tag_name = self.parser.parse_identifier()
                    element_tags.append(VTypes.ElementTag(name=tag_name))
                    if self.parser.head_equals(TokenType.PLUS):
                        self.parser.pop()
                    else:
                        break

            returns: list[VTypes.VType] = []
            if self.parser.head_equals(TokenType.ARROW):
                self.parser.eat(TokenType.ARROW)
                while not self.parser.head_equals(TokenType.LEFT_BRACE):
                    return_type = self.parser.parse_type()
                    returns.append(return_type)
                    if self.parser.head_equals(TokenType.COMMA):
                        self.parser.eat(TokenType.COMMA)
                    else:
                        break

            body = self.parser.parse_block()
            return DefineNode(
                location_token.location,
                generics,
                name,
                element_tags,
                parameters,
                returns,
                body,
            )

    class ObjectParser(ParserStrategy):
        name: str = "Object"

        def can_parse(self) -> bool:
            return self.go(TokenType.OBJECT)

        def parse(self) -> ASTNode:
            location_token = self.parser.pop()

            generics: list[VType] = []
            if self.parser.head_equals(TokenType.LEFT_SQUARE):
                generics = self.parser.parse_generics()
                self.parser.eat(TokenType.RIGHT_SQUARE)

            object_name = self.parser.parse_identifier()

            default_constructor: list[tuple[FieldNode, Optional[ASTNode]]] | None = None
            if self.parser.head_equals(TokenType.LEFT_PAREN):
                default_constructor = []
                self.parser.eat(TokenType.LEFT_PAREN)
                while not self.parser.head_equals(TokenType.RIGHT_PAREN):
                    visibility_modifier: Visibility | None = None
                    if self.parser.head_in(
                        TokenType.PRIVATE, TokenType.READABLE, TokenType.PUBLIC
                    ):
                        visibility_modifier = Visibility(self.parser.pop().value)
                    self.parser.eat(TokenType.VARIABLE)
                    field_name = self.parser.parse_identifier_fragment()
                    if not self.parser.eat(
                        TokenType.COLON,
                        f"Expected type after field name {field_name.name}",
                    ):
                        self.parser.sync(
                            TokenType.EQUALS, TokenType.COMMA, TokenType.RIGHT_PAREN
                        )
                        field_type = VTypes.ErrorType()
                    else:
                        field_type = self.parser.parse_type()
                    field_value: ASTNode | None = None
                    if self.parser.head_equals(TokenType.EQUALS):
                        self.parser.eat(TokenType.EQUALS)
                        field_value = self.parser.parse_next()
                    default_constructor.append(
                        (
                            FieldNode(
                                field_name.location,
                                visibility_modifier or Visibility.READABLE,
                                field_name,
                                field_type,
                            ),
                            field_value,
                        )
                    )
                    if self.parser.head_equals(TokenType.COMMA):
                        self.parser.eat(TokenType.COMMA)
                    else:
                        break
                self.parser.eat(TokenType.RIGHT_PAREN)

            trait_implemented: VType | None = None
            if self.parser.head_equals(TokenType.AS):
                self.parser.discard()
                trait_implemented = self.parser.parse_type()

            if default_constructor and trait_implemented:
                # If there is a default constructor, this object will be analysed
                # as if it were a normal object. BUT, still add an error
                self.parser.add_error(
                    "Cannot have default constructor and trait implementation at the same time",
                    location_token,
                )
                trait_implemented = None

            fields: list[FieldNode] = []
            members: list[MemberNode] = []
            methods: list[DefineNode] = []

            if not self.parser.eat(TokenType.LEFT_BRACE):
                self.parser.sync(TokenType.RIGHT_BRACE)
                return ErrorNode(location_token.location, location_token)

            # Manually parse until RIGHT_BRACE because just normal
            # parse_block does not capture the semantic details
            # of an object definition
            while not self.parser.head_equals(TokenType.RIGHT_BRACE):
                # Store whether the next member/field/method is visibility modified.
                visibility_modifier: Visibility | None = None
                if self.parser.head_in(
                    TokenType.PRIVATE, TokenType.READABLE, TokenType.PUBLIC
                ):
                    visibility_modifier = Visibility(self.parser.pop().value)

                if self.parser.head_equals(TokenType.FIELD):
                    self.parser.discard()
                    if trait_implemented:
                        self.parser.add_error(
                            "Cannot define new field in trait implementation.",
                            location_token.location,
                        )
                    field_name = self.parser.parse_identifier_fragment()
                    self.parser.eat(TokenType.COLON)
                    field_type = self.parser.parse_type()
                    fields.append(
                        FieldNode(
                            field_name.location,
                            visibility_modifier or Visibility.READABLE,
                            field_name,
                            field_type,
                        )
                    )
                elif self.parser.head_equals(TokenType.VARIABLE):
                    if trait_implemented:
                        self.parser.add_error(
                            "Cannot declare/set members in trait implementation",
                            location_token.location,
                        )
                    variable_node = self.parser.VariableParser(self.parser).parse()
                    if not trait_implemented and not isinstance(
                        variable_node, VariableSetNode
                    ):
                        # Only report an error if it's plausible for the error to exist
                        self.parser.add_error(
                            "Member must be given value in object definition",
                            variable_node.location,
                        )
                    else:
                        # assert for type checker
                        assert isinstance(variable_node, VariableSetNode)
                        members.append(
                            MemberNode(
                                variable_node.location,
                                visibility_modifier or Visibility.READABLE,
                                variable_node.name,
                                variable_node.value,
                            )
                        )
                elif self.parser.head_equals(TokenType.DEFINE):
                    method = self.parser.DefineParser(self.parser).parse()
                    if visibility_modifier == Visibility.READABLE:
                        self.parser.add_error(
                            "Object method can only be public or private. A 'readable' method makes no sense",
                            method.location,
                        )
                    assert isinstance(method, DefineNode)
                    method = replace(
                        method, visibility=visibility_modifier or Visibility.PUBLIC
                    )
                    methods.append(method)
                elif self.parser.SkipTokenParser(self.parser).can_parse():
                    self.parser.discard()
                else:
                    self.parser.add_error(
                        f"Unexpected item in ~~bagging area~~ object definition. Expected field/member/define. Found {self.parser.head()}",
                        self.parser.head().location,
                    )
                    self.parser.sync(
                        TokenType.RIGHT_BRACE,
                        TokenType.VARIABLE,
                        TokenType.FIELD,
                        TokenType.PUBLIC,
                        TokenType.READABLE,
                        TokenType.PRIVATE,
                        TokenType.DEFINE,
                    )
            self.parser.eat(TokenType.RIGHT_BRACE)
            if trait_implemented:
                return ObjectTraitImplNode(
                    location_token.location,
                    generics,
                    object_name,
                    trait_implemented,
                    methods,
                )
            else:
                return ObjectDefinitionNode(
                    location_token.location,
                    generics,
                    object_name,
                    fields,
                    members,
                    default_constructor,
                    methods,
                )

    class AsParser(ParserStrategy):
        name: str = "As Expression"

        def can_parse(self) -> bool:
            return self.go(TokenType.AS)

        def parse(self) -> ASTNode:
            as_token = self.parser.pop()  # Pop the 'as' token
            type_ = self.parser.parse_type()
            return SafeTypeCastNode(as_token.location, type_)

    class AsUnsafeParser(ParserStrategy):
        name: str = "As Unsafe Expression"

        def can_parse(self) -> bool:
            return self.go(TokenType.AS_UNSAFE)

        def parse(self) -> ASTNode:
            as_token = self.parser.pop()  # Pop the 'as_unsafe' token
            type_ = self.parser.parse_type()
            return UnsafeTypeCastNode(as_token.location, type_)

    class ImportParser(ParserStrategy):
        name: str = "Import Statement"

        def can_parse(self) -> bool:
            return self.go(TokenType.IMPORT)

        def parse(self) -> ASTNode:
            import_token = self.parser.pop()  # Pop the 'import' token
            module_name = self.parser.parse_identifier()
            if not self.parser.head_equals(TokenType.AS):
                return ModuleImportNode(import_token.location, module_name)
            self.parser.eat(TokenType.AS)  # Pop the 'as' token
            alias_name = self.parser.parse_identifier()
            return AliasedImportNode(import_token.location, module_name, alias_name)

    class TraitParser(ParserStrategy):
        name: str = "Trait Definition"

        # Note that traits can implement other traits, just like objects.

        def can_parse(self) -> bool:
            return self.go(TokenType.TRAIT)

        def parse(self) -> ASTNode:
            location_token = self.parser.pop()  # Pop the 'trait' token

            generics: list[VTypes.VType] = []

            if self.parser.head_equals(TokenType.LEFT_SQUARE):
                generics = self.parser.parse_generics()
                self.parser.eat(TokenType.RIGHT_SQUARE)

            trait_name = self.parser.parse_identifier()

            parent_trait: VType | None = None
            if self.parser.head_equals(TokenType.AS):
                self.parser.discard()
                parent_trait = self.parser.parse_type()

            required_methods: list[DefineNode] = []
            default_methods: list[DefineNode] = []

            if not self.parser.eat(TokenType.LEFT_BRACE):
                self.parser.sync(TokenType.RIGHT_BRACE)
                return ErrorNode(location_token.location, location_token)

            # Manually parse until RIGHT_BRACE because just normal
            # parse_block does not capture the semantic details
            # of a trait definition
            while not self.parser.head_equals(TokenType.RIGHT_BRACE):
                if self.parser.head_equals(TokenType.DEFINE):
                    method = self.parser.DefineParser(self.parser).parse()
                    assert isinstance(method, DefineNode)
                    if isinstance(method.body, AuxiliaryNode):
                        required_methods.append(method)
                    else:
                        default_methods.append(method)
                elif self.parser.SkipTokenParser(self.parser).can_parse():
                    self.parser.discard()
                else:
                    self.parser.add_error(
                        f"Unexpected item in trait definition. Expected define. Found {self.parser.head()}",
                        self.parser.head().location,
                    )
                    self.parser.sync(
                        TokenType.RIGHT_BRACE,
                        TokenType.DEFINE,
                    )
            self.parser.eat(TokenType.RIGHT_BRACE)

            if parent_trait:
                return TraitImplTraitNode(
                    location_token.location,
                    generics,
                    trait_name,
                    parent_trait,
                    required_methods,
                    default_methods,
                )
            else:
                return TraitNode(
                    location_token.location,
                    generics,
                    trait_name,
                    required_methods,
                    default_methods,
                )

    class MatchExpressionParser(ParserStrategy):
        name: str = "Match Expression"

        def can_parse(self) -> bool:
            return self.go(TokenType.MATCH)

        def parse(self) -> ASTNode:
            location_token = self.parser.pop()  # Pop the 'match' token
            if not self.parser.eat(TokenType.LEFT_BRACE):
                self.parser.sync(TokenType.RIGHT_BRACE)
                return ErrorNode(location_token.location, location_token)

            branches: list[MatchBranch] = []
            while not self.parser.head_equals(TokenType.RIGHT_BRACE):
                # Parse a single branch of the match expression
                # First, get all the cases before the arrow
                cases: list[MatchBranch] = []
                while not self.parser.head_equals(TokenType.ARROW):
                    match (self.parser.head().type):
                        case TokenType.EXACTLY:
                            cases.append(self.exact_case())
                        case TokenType.AS:
                            cases.append(self.as_case())
                        case TokenType.IF:
                            cases.append(self.if_case())
                        case TokenType.PATTERN:
                            cases.append(self.pattern_case())
                        case TokenType.UNDERSCORE:
                            cases.append(MatchDefaultBranch())
                            self.parser.discard()
                        case _:
                            self.parser.add_error(
                                f"Unexpected token in match branch: {self.parser.head()}",
                                self.parser.head(),
                            )
                            self.parser.discard()
                            self.parser.sync(TokenType.COMMA, TokenType.ARROW)
                    if self.parser.head_equals(TokenType.COMMA):
                        self.parser.eat(TokenType.COMMA)

                if not self.parser.eat(TokenType.ARROW):  # Pop the ARROW token
                    self.parser.sync(TokenType.COMMA, TokenType.RIGHT_BRACE)
                    continue
                # Now, parse the body of the branch
                body = group_wrap(
                    self.parser.parse_until(TokenType.COMMA, TokenType.RIGHT_BRACE)
                )

                for case in cases:
                    case.body = body
                    branches.append(case)
                if self.parser.head_equals(TokenType.COMMA):
                    self.parser.eat(TokenType.COMMA)
            self.parser.eat(TokenType.RIGHT_BRACE)
            return MatchNode(location_token.location, branches)

        def exact_case(self) -> MatchExactBranch:
            self.parser.eat(TokenType.EXACTLY)  # Pop the 'exactly' token
            values: list[ASTNode] = []
            while True:
                value = group_wrap(
                    self.parser.parse_until(
                        TokenType.PIPE, TokenType.COMMA, TokenType.ARROW
                    )
                )
                values.append(value)
                if self.parser.head_equals(TokenType.PIPE):
                    self.parser.eat(TokenType.PIPE)
                else:
                    break
            return MatchExactBranch(values)

        def as_case(self) -> MatchAsBranch:
            self.parser.eat(TokenType.AS)  # Pop the 'as' token
            name = Identifier()
            if self.parser.head_in(TokenType.WORD, TokenType.UNDERSCORE):
                name = self.parser.parse_identifier()

            type_: VType | None = None
            if self.parser.head_equals(TokenType.COLON):
                self.parser.eat(TokenType.COLON)
                type_ = self.parser.parse_type()

            if self.parser.head_equals(TokenType.IF):
                self.parser.eat(TokenType.IF)
                predicate = group_wrap(
                    self.parser.parse_until(TokenType.COMMA, TokenType.ARROW)
                )
                return MatchAsBranch(name, type_, predicate)

            return MatchAsBranch(name, type_)

        def if_case(self) -> MatchIfBranch:
            self.parser.eat(TokenType.IF)  # Pop the 'if' token
            condition = group_wrap(
                self.parser.parse_until(TokenType.COMMA, TokenType.ARROW)
            )
            return MatchIfBranch(condition)

        def pattern_case(self) -> MatchPatternBranch:
            self.parser.eat(TokenType.PATTERN)  # Pop the 'pattern' token
            pattern: MatchPattern
            if self.parser.head_equals(TokenType.STRING):
                pattern = StringPattern(self.parser.parse_next())
            elif self.parser.head_equals(TokenType.LEFT_SQUARE):
                pattern = ListPattern(self.parse_pattern(TokenType.RIGHT_SQUARE))
            elif self.parser.head_equals(TokenType.LEFT_PAREN):
                pattern = TuplePattern(self.parse_pattern(TokenType.RIGHT_PAREN))
            else:
                self.parser.add_error(
                    f"Unexpected token in pattern match: {self.parser.head()}",
                    self.parser.head(),
                )
                pattern = ErrorPattern()
                self.parser.sync(TokenType.COMMA, TokenType.ARROW)
            predicate: ASTNode | None = None
            if self.parser.head_equals(TokenType.IF):
                self.parser.eat(TokenType.IF)
                predicate = group_wrap(
                    self.parser.parse_until(TokenType.COMMA, TokenType.ARROW)
                )
            return MatchPatternBranch(pattern, predicate)

        def parse_pattern(self, end_token_type: TokenType) -> list[PatternComponent]:
            self.parser.discard()  # Remove the opening token
            items: list[PatternComponent] = []
            while not self.parser.head_equals(end_token_type):
                # First, check if this is a named wildcard or greedy
                # pattern component
                if self.parser.head_equals(TokenType.VARIABLE):
                    self.parser.discard()
                    variable_name = self.parser.parse_identifier_fragment()

                    # If there's no equals, then just consume until
                    # comma or closing, and push an ASTComponent
                    if not self.parser.head_equals(TokenType.EQUALS):
                        value = group_wrap(
                            [VariableGetNode(variable_name.location, variable_name)]
                            + self.parser.parse_until(TokenType.COMMA, end_token_type)
                        )
                        items.append(ASTComponent(value))
                    else:
                        # It's either a wildcard or greedy component
                        self.parser.eat(TokenType.EQUALS)
                        if self.parser.head_equals(TokenType.UNDERSCORE):
                            self.parser.eat(TokenType.UNDERSCORE)
                            items.append(WildcardComponent(variable_name))
                        elif self.parser.head_equals(TokenType.PASS):
                            self.parser.eat(TokenType.PASS)
                            items.append(GreedyComponent(variable_name))
                        else:
                            self.parser.add_error(
                                f"Expected '_' or '*' after '=' in pattern component. Found {self.parser.head()}",
                                self.parser.head(),
                            )
                            self.parser.sync(TokenType.COMMA, end_token_type)
                # Next, check for unnamed wildcard or greedy
                elif self.parser.head_equals(TokenType.UNDERSCORE):
                    self.parser.eat(TokenType.UNDERSCORE)
                    items.append(WildcardComponent(None))
                elif self.parser.head_equals(TokenType.PASS):
                    self.parser.eat(TokenType.PASS)
                    items.append(GreedyComponent(None))
                else:
                    value = group_wrap(
                        self.parser.parse_until(TokenType.COMMA, end_token_type)
                    )
                    items.append(ASTComponent(value))
                if self.parser.head_equals(TokenType.COMMA):
                    self.parser.eat(TokenType.COMMA)
            self.parser.eat(end_token_type)
            return items

    class AssertParser(ParserStrategy):
        name: str = "Assert Expression"

        def can_parse(self):
            return self.go(TokenType.ASSERT)

        def parse(self):
            location_token = self.parser.pop()  # Pop the 'assert' token
            condition = self.parser.parse_block()
            if not is_expressionable([condition]):
                self.parser.add_error(
                    "Assert condition must be an expression", condition.location
                )
                return ErrorNode(location_token.location, location_token)

            if not self.parser.head_equals(TokenType.ELSE):
                return AssertNode(location_token.location, condition)

            self.parser.eat(TokenType.ELSE)  # Pop the 'else' token
            else_block = self.parser.parse_block()
            return AssertElseNode(location_token.location, condition, else_block)

    class BreakParser(ParserStrategy):
        name: str = "Break Statement"

        def can_parse(self) -> bool:
            return self.go(TokenType.BREAK)

        def parse(self) -> ASTNode:
            location_token = self.parser.pop()  # Pop the 'break' token
            if not self.parser.head_equals(TokenType.LEFT_PAREN):
                return BreakNode(location_token.location, None)

            values = self.parser.parse_items(
                TokenType.LEFT_PAREN,
                TokenType.COMMA,
                TokenType.RIGHT_PAREN,
                self.parser.parse_next,
                lambda x: not is_expressionable([x]),
                lambda _: ErrorNode(location_token.location, location_token),
            )
            return BreakNode(location_token.location, values)

    class TagCreationParser(ParserStrategy):
        name: str = "Tag Creation"

        def can_parse(self) -> bool:
            return self.parser.head_in(
                TokenType.TAG_COMPANION,
                TokenType.TAG_CONSTRUCTED,
                TokenType.TAG_COMPUTED,
                TokenType.TAG_ELEMENT,
                TokenType.TAG_VARIANT,
                TokenType.TAG_EXTEND,
            )

        def parse(self) -> ASTNode:
            category_token = self.parser.pop()

            # If this is a tag extension, there won't be a tag category
            # otherwise, set it based on the token
            tag_category: TagCategory | None = None
            if not category_token.type == TokenType.TAG_EXTEND:
                tag_category = TagCategories.tag_category_from_token(
                    category_token.value
                )
            self.parser.eat(TokenType.HASH)  # Eat the # token
            tag_name = self.parser.parse_identifier()
            if tag_category in [TagCategory.ELEMENT, TagCategory.COMPANION]:
                return TagCreationNode(
                    category_token.location, tag_name, tag_category, []
                )

            overlays: list[OverlayRule] = []
            if self.parser.head_equals(TokenType.LEFT_BRACE, care_about_eof=False):
                self.parser.discard()  # Discard LEFT_BRACE
                while not self.parser.head_equals(TokenType.RIGHT_BRACE):
                    elements: list[Identifier] = []
                    if self.parser.head_equals(TokenType.WORD):
                        elements.append(self.parser.parse_identifier(*ELEMENT_TOKENS))
                    else:
                        elements = self.parser.parse_items(
                            TokenType.LEFT_PAREN,
                            TokenType.COMMA,
                            TokenType.RIGHT_PAREN,
                            lambda: self.parser.parse_identifier(*ELEMENT_TOKENS),
                            lambda ident: ident.error,
                            lambda token: Identifier(token.location, is_error=True),
                            singleton=True,
                        )
                        self.parser.eat(TokenType.RIGHT_PAREN)
                    generics: list[VType] = []

                    if self.parser.head_equals(TokenType.LEFT_SQUARE):
                        generics = self.parser.parse_generics()
                        self.parser.eat(TokenType.RIGHT_SQUARE)

                    if not self.parser.eat(TokenType.COLON):
                        self.parser.sync(TokenType.COMMA, TokenType.RIGHT_BRACE)

                    # Tuple = input types -> output types
                    rules: list[Tuple[list[VType], list[VType]]] = []
                    if self.parser.head_equals(TokenType.LEFT_BRACE):
                        self.parser.discard()  # Discard LEFT_BRACE
                        while not self.parser.head_equals(TokenType.RIGHT_BRACE):
                            rules.append(self.parse_overlay_rule())
                            if self.parser.head_equals(TokenType.COMMA):
                                self.parser.eat(TokenType.COMMA)
                        self.parser.eat(TokenType.RIGHT_BRACE)
                    else:
                        rules.append(self.parse_overlay_rule())
                    for element in elements:
                        for input_types, output_types in rules:
                            overlays.append(
                                OverlayRule(
                                    element,
                                    generics,
                                    input_types,
                                    output_types,
                                )
                            )
                self.parser.eat(TokenType.RIGHT_BRACE)
            if (
                tag_category is None
            ):  # Tag category is None only if this is a tag extension
                return TagExtendNode(category_token.location, tag_name, overlays)
            return TagCreationNode(
                category_token.location, tag_name, tag_category, overlays
            )

        def parse_overlay_rule(self) -> Tuple[list[VType], list[VType]]:
            input_types: list[VType] = []
            output_types: list[VType] = []

            self.parser.eat(TokenType.LEFT_PAREN)
            while not self.parser.head_equals(TokenType.RIGHT_PAREN):
                input_types.append(self.parser.parse_type())
                if self.parser.head_equals(TokenType.COMMA):
                    self.parser.eat(TokenType.COMMA)
            self.parser.eat(TokenType.RIGHT_PAREN)

            if not self.parser.eat(TokenType.ARROW):
                self.parser.sync(TokenType.COMMA, TokenType.RIGHT_BRACE)

            if not self.parser.head_equals(TokenType.LEFT_PAREN):
                output_types.append(self.parser.parse_type())
            else:
                self.parser.eat(TokenType.LEFT_PAREN)
                while not self.parser.head_equals(TokenType.RIGHT_PAREN):
                    output_types.append(self.parser.parse_type())
                    if self.parser.head_equals(TokenType.COMMA):
                        self.parser.eat(TokenType.COMMA)
                self.parser.eat(TokenType.RIGHT_PAREN)

            return (input_types, output_types)

    class TagDisjointParser(ParserStrategy):
        name: str = "Tag Disjoint Declaration"

        def can_parse(self) -> bool:
            return self.go(TokenType.TAG_DISJOINT)

        def parse(self) -> ASTNode:
            location_token = self.parser.pop()  # Pop the 'tag disjoint' token
            self.parser.eat(TokenType.HASH)  # Eat the # token
            parent_tag = self.parser.parse_identifier()
            self.parser.eat(TokenType.HASH)
            child_tag = self.parser.parse_identifier()
            return TagDisjointNode(location_token.location, parent_tag, child_tag)
