from lexer.TokenType import TokenType


class Token:
    def __init__(self, tokentype: TokenType, value: str, line: int, column: int):
        self.tokentype = tokentype
        self.value = value
        self.line = line
        self.column = column
    
    def __repr__(self):
        return f"Token({self.tokentype}, {self.value}, {self.line}, {self.column})"