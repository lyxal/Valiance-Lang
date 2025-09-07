from typing import Callable
from lexer.TokenType import TokenType
from lexer.Token import Token
import re

NEWLINE = "\n"
DECIMAL_SEPARATOR = "."
SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'
BACKSLASH = "\\"
COMMA = ","
COLON = ":"

VARIABLE_GET = "$"
VARIABLE_SET = "~>"
LIST_OPEN = "["
LIST_CLOSE = "]"
FUNCTION_OPEN = "{"
FUNCTION_CLOSE = "}"
FUNCTION_RETURN_TYPE_SEPARATOR = "->"
FUNCTION_BODY_SEPARATOR = "=>"

ELEMENT_CHARACTERS = r"[a-zA-Z0-9_+<>=*/\-^%$#@!?|&\\]"

class Lexer:
    # Adapted from https://github.com/Vyxal/Vyxal/blob/version-3/shared/src/vyxal/parsing/Lexer.scala

    def __init__(self, text: str):
        self.program: list[str] = list(text)
        self.line = self.column = 1
        self.tokens: list[Token] = []

    def pop(self, n: int = 1) -> str:
        result = ""
        for _ in range(n):
            if not self.program: break
            char = self.program[0]
            self.program = self.program[1:]
            result += char
            if char == NEWLINE:
                self.line += 1
                self.column = 1
            else:
                self.column += 1

        return result
    
    def peek(self, n: int = 1) -> str:
        return ''.join(self.program[:n])
    
    def safeCheck(self, predicate: Callable[[str], bool]) -> bool:
        if not self.program:
            return False
        return len(self.program) > 0 and predicate(self.program[0])

    def headEqual(self, string: str) -> bool:
        return self.peek(len(string)) == string

    def headMatch(self, pattern: str) -> bool:
        return re.match(pattern, "".join(self.program)) is not None

    def headIsDigit(self) -> bool:
        return self.safeCheck(lambda c: c.isdigit())
    
    def headIsAlpha(self) -> bool:
        return self.safeCheck(lambda c: c.isalpha())

    def headIsWhitespace(self) -> bool:
        return self.safeCheck(lambda c: c.isspace())

    def headIn(self, chars: str|list[str]) -> bool:
        return self.safeCheck(lambda c: c in chars)
    
    def quickToken(self, tokentype: TokenType, value: str):
        token = Token(tokentype, value, self.line, self.column)
        self.tokens.append(token)
        self.pop(len(value))

    def addToken(self, tokentype: TokenType, value: str, line: int, column: int):
        token = Token(tokentype, value, line, column)
        self.tokens.append(token)

    def eat(self, value: str):
        if self.headEqual(value):
            self.pop(len(value))
        else:
            raise Exception(f"Expected '{value}' at position {self.line}:{self.column}, found '{self.peek(len(value))}'")
    
    def eatWhitespace(self):
        while self.headIsWhitespace():
            self.pop()

    def simpleName(self) -> str:
        name = ""
        while self.headIsAlpha() or self.headIsDigit() or self.headEqual("_"):
            name += self.pop()
        return name

    @staticmethod
    def tokenise(program: str) -> list[Token]:
        lexer = Lexer(program)
        return lexer.lex()
    
    def lex(self) -> list[Token]:
        while self.program:
            if self.headIsDigit() or self.headMatch(r"-[1-9]"): self.lexNumber()
            elif self.headEqual(NEWLINE): self.pop()
            elif self.headIsWhitespace(): self.pop()
            elif self.headEqual(DOUBLE_QUOTE): self.lexString()
            elif self.headEqual(VARIABLE_GET): self.quickToken(TokenType.VARIABLE_GET, VARIABLE_GET)
            elif self.headEqual(VARIABLE_SET): self.quickToken(TokenType.VARIABLE_SET, VARIABLE_SET)
            elif self.headEqual(LIST_OPEN): self.quickToken(TokenType.LIST_OPEN, LIST_OPEN)
            elif self.headEqual(LIST_CLOSE): self.quickToken(TokenType.LIST_CLOSE, LIST_CLOSE)
            elif self.headEqual(FUNCTION_OPEN): self.lexFunctionTokens()
            elif self.headEqual(COLON): self.quickToken(TokenType.COLON, COLON)
            elif self.safeCheck(lambda c: re.match(ELEMENT_CHARACTERS, c) is not None): self.lexElement()
            else:
                start = (self.line, self.column)
                unknown_char = self.pop()
                self.addToken(TokenType.UNKNOWN, unknown_char, *start)

        return self.tokens

    def lexNumber(self):
        start = (self.line, self.column)
        if self.peek() == "0":
            self.quickToken(TokenType.NUMBER, "0")
            return
        
        number = ""
        
        if self.headEqual("-"):
            self.pop()
            number += "-"

        number += self.decimalNumber()
        if self.headMatch(r"i\d+"):
            self.eat("i")
            imaginary_part = self.decimalNumber()
            number += "i" + imaginary_part

        self.addToken(TokenType.NUMBER, number, *start)

    def decimalNumber(self) -> str:
        number: str = ""

        if self.headIsDigit(): number += self.simpleNumber()
        if self.headEqual(DECIMAL_SEPARATOR):
            number += self.pop()
            if self.headIsDigit(): number += self.simpleNumber()
            else: raise Exception(f"Expected digit after decimal point at line {self.line}, column {self.column}")

        return number

    def simpleNumber(self) -> str:
        number = ""
        while self.headIsDigit():
            number += self.pop()
        return number

    def lexString(self):
        start = (self.line, self.column)
        self.eat(DOUBLE_QUOTE)
        string_content = ""
        while self.program and not self.headEqual(DOUBLE_QUOTE):
            if self.headEqual(BACKSLASH):
                self.eat(BACKSLASH)
                if not self.program:
                    raise Exception(f"Unfinished escape sequence at line {self.line}, column {self.column}")
                escape_char = self.pop()
                if escape_char == "n":
                    string_content += "\n"
                elif escape_char == "t":
                    string_content += "\t"
                elif escape_char == DOUBLE_QUOTE:
                    string_content += DOUBLE_QUOTE
                elif escape_char == BACKSLASH:
                    string_content += BACKSLASH
                else:
                    string_content += escape_char
            else:
                string_content += self.pop()
        self.eat(DOUBLE_QUOTE)
        self.addToken(TokenType.STRING, string_content, *start)

    def lexElement(self):
        start = (self.line, self.column)
        element = ""
        while self.safeCheck(lambda c: re.match(ELEMENT_CHARACTERS, c) is not None):
            element += self.pop()
        self.addToken(TokenType.ELEMENT, element, *start)

    def lexFunctionTokens(self):
        self.quickToken(TokenType.FUNCTION_OPEN, FUNCTION_OPEN)
        if not self.headEqual(COLON):
            return # A function without arguments, so can safely ignore
        
        self.quickToken(TokenType.COLON, COLON)
        self.eatWhitespace()
        while not (self.headEqual(FUNCTION_RETURN_TYPE_SEPARATOR) or self.headEqual(FUNCTION_BODY_SEPARATOR)):
            if self.headIsWhitespace():
                self.pop()
            elif self.headIsAlpha() or self.headEqual("_"):
                start = (self.line, self.column)
                name = self.simpleName()
                self.addToken(TokenType.NAME, name, *start)
                self.eatWhitespace()
                if self.headEqual(COLON):
                    self.eat(COLON)
                    self.eatWhitespace()
                    typeStart = (self.line, self.column)
                    typeName = self.simpleName()
                    self.addToken(TokenType.TYPE, typeName, *typeStart)
            elif self.headEqual(COLON):
                self.eat(COLON)
                self.eatWhitespace()
                start = (self.line, self.column)
                typeName = self.simpleName()
                self.addToken(TokenType.TYPE, typeName, *start)
            elif self.headEqual(COMMA):
                self.quickToken(TokenType.COMMA, COMMA)
            else:
                raise Exception(f"Unexpected character in function argument list at line {self.line}, column {self.column}: '{self.peek()}'")

        self.eatWhitespace()

        if self.headEqual(FUNCTION_RETURN_TYPE_SEPARATOR):
            self.quickToken(TokenType.FUNCTION_RETURN_TYPE_SEPARATOR, FUNCTION_RETURN_TYPE_SEPARATOR)
            self.eatWhitespace()
            start = (self.line, self.column)
            returnType = self.simpleName()
            self.addToken(TokenType.TYPE, returnType, *start)

        self.eatWhitespace()
        self.quickToken(TokenType.FUNCTION_BODY_SEPARATOR, FUNCTION_BODY_SEPARATOR)


