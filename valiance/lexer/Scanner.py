from typing import Callable, TypeVar
from valiance.lexer.Token import Token
from valiance.lexer.TokenType import TokenType
import string

T = TypeVar("T")

ELEMENT_FIRST_CHARS = string.ascii_letters + "-+*%&^!/=<>"
ELEMENT_CHARS = ELEMENT_FIRST_CHARS + "_." + string.digits + "~?"

RESERVED_WORDS = (
    "above",
    "any",
    "as",
    "async",
    "await",
    "call",
    "concurrent",
    "define",
    "fn",
    "foreach",
    "if",
    "implements",
    "import",
    "match",
    "object",
    "parallel",
    "private",
    "public",
    "readable",
    "self",
    "spawn",
    "this",
    "trait",
    "variant",
    "where",
    "while",
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


class Scanner:
    """
    Notice: A method starting with an underscore (_) does NOT
    update the line and column numbers.

    Methods starting with `scan`, and are called directly by scan_tokens()
    must add tokens at the end of their logic, rather than returning a
    value back to scan_tokens().
    """

    def __init__(self, source: str):
        self.source = source
        self.characters = list(source)
        self.tokens: list[Token] = []
        self.line, self.column = 1, 1

    def advance(self) -> str:
        """
        Pop the first character from the character list and return it.

        If the character is a newline, the line and column numbers
        will be updated accordingly.

        :return: The popped character.
        """
        char = self.characters.pop(0)
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def add_token(self, type_: TokenType, value: str):
        """
        Create a new token and add it to the token list.

        Removes the token's value from the source string
        and updates the column number.

        :param type_: The type of the token.
        :param value: The value of the token.
        :return: None
        """
        token = Token(type_, value, self.line, self.column)
        self.tokens.append(token)
        self.characters = self.characters[len(value) :]
        self.column += len(value)

    def _add_token(self, type_: TokenType, value: str, line: int, column: int):
        """
        Create a new token and add it to the token list.

        Does NOT remove the token's value from the source string
        or update the column number.

        Useful for flexible token creation without affecting
        the current scanning state.

        :param type_: The type of the token.
        :param value: The value of the token.
        :param line: The line number of the token.
        :param column: The column number of the token.
        :return: None
        """
        token = Token(type_, value, line, column)
        self.tokens.append(token)

    def _discard(self, n: int = 1):
        """
        Pop the first character from the character list without
        caring about its value.

        :param self: The Scanner instance.
        :param n: The number of characters to discard.
        """
        for _ in range(n):
            self.characters.pop(0)

    def _head_equals(self, string: str) -> bool:
        """
        Check if the start of the character list matches a given string.

        :param string: The string to compare against.
        :return: True if the start of the character list matches the string, False otherwise.
        """
        return unwrap_and_test(self._peek(len(string)), lambda s: s == string)

    def _head_matches(self, pattern: str) -> bool:
        """
        Check if the start of the character list matches a given regex pattern.

        :param self: The Scanner instance.
        :param pattern: The regex pattern to match against.
        :return: True if the start of the character list matches the pattern, False otherwise.
        :rtype: bool
        """

        import re

        pobj = re.compile(pattern)
        mobj = pobj.match("".join(self.characters))
        return mobj is not None

    def _peek(self, n: int = 1) -> str | None:
        """
        Peek at the first n characters in the character list.

        :param n: The number of characters to peek at.
        :return: The first n characters as a string, or None if there are not enough
        """
        if n - 1 < len(self.characters):
            return "".join(self.characters[:n])
        return None

    def scan_tokens(self) -> list[Token]:
        while self.characters:
            HEAD = self.characters[0]
            match HEAD:
                case " " | "\r" | "\t":
                    self._discard()
                    self.column += 1
                case "\n":
                    self.add_token(TokenType.NEWLINE, HEAD)
                    self.line += 1
                    self.column = 1
                case _ if HEAD.isdecimal() or self._head_matches(r"-\d"):
                    self.scan_number()
                case "=" if not self._head_equals("=="):
                    self.add_token(TokenType.EQUALS, "=")
                case _ if HEAD in ELEMENT_FIRST_CHARS:
                    self.scan_element()
                case "$":
                    self.scan_variable()
                case "(":
                    self.add_token(TokenType.LEFT_PAREN, HEAD)
                case ")":
                    self.add_token(TokenType.RIGHT_PAREN, HEAD)
                case "[":
                    self.add_token(TokenType.LEFT_SQUARE, HEAD)
                case "]":
                    self.add_token(TokenType.RIGHT_SQUARE, HEAD)
                case "{":
                    self.add_token(TokenType.LEFT_BRACE, HEAD)
                case "}":
                    self.add_token(TokenType.RIGHT_BRACE, HEAD)
                case ",":
                    self.add_token(TokenType.COMMA, HEAD)
                case _ if self._head_equals("->"):
                    self.add_token(TokenType.ARROW, "->")
                case ":":
                    self.add_token(TokenType.COLON, ":")
                case "@":
                    self.scan_annotation()
                case _ if self._head_equals("#:"):
                    # Comment, discard until newline

                    while self.characters and self.characters[0] != "\n":
                        self._discard()
                    # Newline will be handled in the next iteration
                case _ if self._head_equals("#{"):
                    # Multiline comment
                    start_line, start_column = self.line, self.column
                    while self.characters and not self._head_equals("}#"):
                        self._discard()
                    # Discard the closing sequence
                    if self._head_equals("}#"):
                        self._discard(3)
                    else:
                        raise ValueError(
                            f"Unterminated multiline comment starting at line {start_line}, column {start_column}"
                        )
                case '"':
                    # String literal
                    self.scan_string()
                case _:
                    raise ValueError(
                        f'Unexpected character "{HEAD}" at line {self.line}, column {self.column}'
                    )

        return self.tokens + [Token(TokenType.EOF, "", self.line, self.column)]

    def scan_number(self):
        """
        Scan a number token from the character list.
        :return: None
        """
        start_line, start_column = self.line, self.column

        # Scan the real part of the number.
        value = self.scan_decimal()

        # Scan the imaginary part of the number, if it exists.
        if self._head_equals("i"):
            value += self.advance()
            value += self.scan_decimal()

        self._add_token(TokenType.NUMBER, value, start_line, start_column)

    def scan_decimal(self) -> str:
        """
        Scan a decimal number from the character list.
        :return: The scanned decimal number as a string.
        """

        value = ""
        if self._head_equals("-"):
            value += self.advance()

        # Get the integer part, ensuring that multiple leading zeros
        # are treated as different tokens.
        value += self.scan_integer(separate_zeros=True)

        # Get the fractional part, if it exists.
        if self._head_equals("."):
            value += self.advance()
            value += self.scan_integer(separate_zeros=False)

        if value.endswith("."):
            raise ValueError(
                f"Invalid number format at line {self.line}, column {self.column}"
            )

        return value

    def scan_integer(self, separate_zeros: bool) -> str:
        """
        Scan an integer from the character list.
        :param separate_zeros: Whether to immediately stop scanning repeated '0's.
        :return: The scanned integer as a string.
        """
        value = ""
        if separate_zeros and self._head_equals("0"):
            value += self.advance()
            return value
        while unwrap_and_test(self._peek(), lambda c: c in string.digits):
            value += self.advance()
        return value

    def scan_element(self):
        """
        Scan an element token from the character list.
        :return: None
        """
        start_line, start_column = self.line, self.column

        value = ""
        while unwrap_and_test(self._peek(), lambda c: c in ELEMENT_CHARS):
            value += self.advance()

        token_category = (
            TokenType.WORD if value not in RESERVED_WORDS else TokenType[value.upper()]
        )

        self._add_token(token_category, value, start_line, start_column)

    def scan_variable(self):
        """
        Scan a variable token from the character list.
        :return: None
        """
        start_line, start_column = self.line, self.column

        self._discard()  # Discard the '$' character
        value = self.scan_identifier()

        # Allow for an arbitrary number of sub-variable accesses using dots.
        while self._head_equals("."):
            value += self.advance()  # Add the dot
            value += self.scan_identifier()

        self._add_token(TokenType.VARIABLE, value, start_line, start_column)

    def scan_identifier(self) -> str:
        """
        Scan a name identifier from the character list.
        :return: The scanned identifier as a string.
        """

        if not unwrap_and_test(self._peek(), lambda c: c in string.ascii_letters + "_"):
            raise ValueError(
                f"Invalid start of identifier at line {self.line}, column {self.column}"
            )
        value = ""
        while unwrap_and_test(
            self._peek(),
            lambda c: c in string.ascii_letters + string.digits + "_",
        ):
            value += self.advance()
        return value

    def scan_string(self):
        """
        Scan a string literal from the character list.
        :return: None
        """
        start_line, start_column = self.line, self.column

        value = ""
        self._discard()  # Discard the opening quote

        while self.characters and not self._head_equals('"'):
            HEAD = self.characters[0]
            if HEAD == "\\":
                self._discard()
                if not self.characters:
                    raise ValueError(
                        f"Unterminated string literal starting at line {start_line}, column {start_column}"
                    )
                ESCAPE_CHAR = self.advance()
                match ESCAPE_CHAR:
                    case "n":
                        value += "\n"
                    case "t":
                        value += "\t"
                    case "r":
                        value += "\r"
                    case '"':
                        value += '"'
                    case "\\":
                        value += "\\"
                    case _:
                        raise ValueError(
                            f"Invalid escape sequence '\\{ESCAPE_CHAR}' at line {self.line}, column {self.column}"
                        )
            else:
                value += self.advance()

        if not self.characters:
            raise ValueError(
                f"Unterminated string literal starting at line {start_line}, column {start_column}"
            )

        self._discard()  # Discard the closing quote
        self._add_token(TokenType.STRING, value, start_line, start_column)

    def scan_annotation(self):
        """
        Scan an annotation token from the character list.
        :return: None
        """
        start_line, start_column = self.line, self.column

        self._discard()  # Discard the '@' character

        value = self.scan_identifier()

        self._add_token(TokenType.ANNOTATION, value, start_line, start_column)
