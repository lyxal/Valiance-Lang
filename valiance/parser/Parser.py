from abc import abstractmethod
from dataclasses import replace
import itertools
from typing import Callable, Optional, TypeVar
import logging

from valiance.loglib.log_block import log_block
from valiance.parser.Errors import EndOfFileTokenError, GenericParseError, ParserError

from valiance.parser.AST import *
from valiance.lexer.Token import Token
from valiance.lexer.TokenType import TokenType
from valiance.vtypes import VTypes
from valiance.compiler_common.Identifier import Identifier

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

# A helper function to generate a depth-tracking table for
# token synchronisation.
sync_table = lambda: {_type: 0 for _type in OPEN_CLOSE_TOKEN_MAP}

# A helper function to eother wrap a list of ASTNodes into a GroupNode
# or return the single ASTNode if there's only one.

group_wrap: Callable[[list[ASTNode]], ASTNode]
group_wrap = lambda nodes: (
    nodes[0] if len(nodes) == 1 else GroupNode(nodes[0].location, nodes)
)


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


def is_expressionable(nodes: list[ASTNode]) -> bool:
    """Determine if a GroupNode or list of ASTNodes can be treated as an expression.

    Args:
        nodes (GroupNode|list[ASTNode]): The nodes to check. Assumed to be not empty.
    Returns:
        bool: Whether the nodes can be treated as an expression
    """

    if isinstance(nodes, GroupNode):
        nodes = nodes.elements

    for node in nodes:
        if isinstance(node, GroupNode):
            for inner_node in node.elements:
                if not is_expressionable([inner_node]):
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
        for subclass in self.LabelledStackShuffleParser.__subclasses__():
            self.strategies.append(subclass(self))

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

        while self.head_equals(
            TokenType.WHITESPACE, eat_whitespace=False, care_about_eof=False
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

    def parse_identifier(self) -> Identifier:
        identifier = Identifier()
        while self.head_in(
            TokenType.WORD,
            TokenType.UNDERSCORE,
            eat_whitespace=False,
            care_about_eof=False,
        ):
            identifier.name += self.pop().value

        if identifier.name == "":
            self.add_error(
                f"Expected identifier, found {self.head()}", self.head().location
            )
            identifier.error = True

        if self.head_equals(TokenType.DOT, care_about_eof=False):
            self.discard()  # Discard the dot
            self.error_if_eof("Expected property after '.' in identifier.")
            property = self.parse_identifier()
            if property.error:
                identifier.error = True
            else:
                identifier.property = property

        return identifier

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

        postfix_modifiers: list[Token] = []

        if self.lookahead_equals([TokenType.PLUS, TokenType.VARIABLE]):
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
            grouped_modifiers = itertools.groupby(postfix_modifiers)
            for modifier_token, group in grouped_modifiers:
                count = len(list(group))
                match modifier_token.type:
                    case TokenType.PLUS:
                        left = VTypes.ExactRankType(left, count)
                    case TokenType.STAR:
                        left = VTypes.MinimumRankType(left, count)
                    case TokenType.TILDE:
                        left = VTypes.ListType(left, count)
                    case TokenType.QUESTION:
                        for _ in range(count):
                            left = VTypes.OptionalType(left)
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

        # First, handle data tags
        while self.head_equals(TokenType.TAG_TOKEN):
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
            if self.head_equals(TokenType.LEFT_SQUARE):
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
            if self.head_equals(TokenType.COLON):
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

    def parse_parameter_list(self) -> list[Parameter]:
        """Parse a list of parameters to a `fn` or a `define`

        Note: Does NOT account for constructor syntax.

        Returns:
            list[Tuple[str, VTypes.VType]]: The parsed parameters as a list of (name, type) tuples.
        """

        parameters: list[Parameter] = []

        self.eat(TokenType.LEFT_PAREN)

        if self.head_equals(TokenType.RIGHT_PAREN):
            self.discard()
            return parameters

        # Track the number of anonymous generics in this parameter list
        anonymous_generic_id = 0

        while not self.head_equals(TokenType.RIGHT_PAREN):
            # Get the name and type of the parameter
            # Note that name may be empty

            parameter_name = self.parse_identifier()
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

            # Keep a list of all parts of the element name
            # to be combined into a single Identifier later
            names: list[str] = []
            names.append(self.parser.pop().value)
            with log_block("Element Parsing Preamble"):
                logging.debug("Parsing element, head token: %s", names[-1])
                logging.debug("Remaining tokens: %s", self.parser.tokens)

            # After the first token of the element name, EOF isn't actually
            # an error. You may have an element at the end of the file.

            while True:
                self.parser.eat_whitespace()

                if self.parser.head_equals(TokenType.DOT, care_about_eof=False):
                    self.parser.discard()
                    if not is_element_token(
                        self.parser.head(), exclude_underscore=True
                    ):
                        self.parser.add_error(
                            "Expected element name after '.' in multi-part element name.",
                            self.parser.head(),
                        )
                        break
                    names.append("")

                head = self.parser.head_opt()
                if head is None or not is_element_token(head, exclude_underscore=True):
                    break
                with log_block("Element Name Continuation"):
                    logging.debug(
                        "Parsing multi-part element name, current name: %s", names[-1]
                    )
                    logging.debug(
                        "Next token: %s", self.parser.head(eat_whitespace=False)
                    )
                    logging.debug("Remaining tokens: %s", self.parser.tokens)
                names[-1] += self.parser.pop().value

            name = Identifier(names.pop())
            for part in reversed(names):
                name = Identifier(part, property=name)

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

            if self.parser.head_equals(TokenType.LEFT_PAREN, care_about_eof=False):
                arg_nodes = self.parse_element_arguments()
                return ElementNode(
                    location=location_token.location,
                    element_name=name,
                    generics=args,
                    args=arg_nodes,
                    modifier_args=[],
                )

            return ElementNode(
                location=location_token.location,
                element_name=name,
                generics=args,
                args=[],
                modifier_args=[],
            )

        def parse_element_arguments(self) -> list[Tuple[str, ASTNode]]:
            """Parse the arguments for an element.

            Returns:
                list[Tuple[str, ASTNode]]: The parsed arguments as a list of (name, ASTNode) tuples.
            """
            arguments: list[Tuple[str, ASTNode]] = []

            self.parser.pop()

            while not self.parser.head_equals(TokenType.RIGHT_PAREN):
                logger.log(
                    logging.DEBUG,
                    "Parsing element argument, head token: %s",
                    self.parser.head(),
                )
                name = ""
                args: list[ASTNode] = []
                if self.parser.lookahead_equals([TokenType.WORD, TokenType.EQUALS]):
                    name_token = self.parser.pop()
                    name = name_token.value
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
            logger.log(
                logging.DEBUG,
                "Boutta eat RIGHT_PAREN, head token: %s",
                self.parser.head(),
            )
            self.parser.eat(TokenType.RIGHT_PAREN)
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
                generics = self.parser.parse_items(
                    TokenType.LEFT_SQUARE,
                    TokenType.COMMA,
                    TokenType.RIGHT_SQUARE,
                    lambda: VTypes.type_name_to_vtype(
                        self.parser.parse_identifier(), ([], []), [], []
                    ),
                    lambda t: isinstance(t, VTypes.ErrorType),
                    lambda _: VTypes.ErrorType(),
                    singleton=True,
                    validate=None,
                )
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
            variable_name = self.parser.parse_identifier()
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

            values = self.parser.parse_until(
                TokenType.SEMICOLON, TokenType.NEWLINE, TokenType.EOF
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

    class PassParser(ParserStrategy):
        def can_parse(self) -> bool:
            return self.go(TokenType.PASS)

        def parse(self) -> ASTNode:
            return AuxiliaryNode(self.parser.pop().location)
