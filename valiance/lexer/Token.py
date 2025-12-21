from valiance.compiler_common.Location import Location
from valiance.lexer.TokenType import TokenType


class Token:
    def __init__(self, type_: TokenType, value: str, line: int, column: int):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column
        self.location = Location(line, column)

    def __repr__(self):
        return f"Token({self.type}, {self.value}, {self.line}, {self.column})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Token):
            return NotImplemented
        return (
            self.type == other.type
            and self.value == other.value
            and self.line == other.line
            and self.column == other.column
        )
