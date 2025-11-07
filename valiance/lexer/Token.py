from lexer.TokenType import TokenType


class Token:
    def __init__(self, type_: TokenType, value: str, line: int, column: int):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {self.value}, {self.line}, {self.column})"
