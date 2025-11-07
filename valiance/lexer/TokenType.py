import enum


class TokenType(enum.Enum):
    VARIABLE = "VARIABLE"
    WORD = "WORD"
    NUMBER = "NUMBER"
    STRING = "STRING"
    NEWLINE = "NEWLINE"

    # Keywords

    DEFINE = "DEFINE"
    MATCH = "MATCH"
    OBJECT = "OBJECT"
    TRAIT = "TRAIT"
    VARIANT = "VARIANT"
    IMPORT = "IMPORT"
    AS = "AS"
    WHILE = "WHILE"
    FOREACH = "FOREACH"
    IF = "IF"
    THIS = "THIS"
    FN = "FN"
    CALL = "CALL"
    SELF = "SELF"
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    READABLE = "READABLE"
    IMPLEMENTS = "IMPLEMENTS"
    WHERE = "WHERE"

    # Special Symbols
    DUPLICATE = "DUPLICATE"
    SWAP = "SWAP"
    POP = "POP"
    LEFT_PAREN = "LEFT_PAREN"
    RIGHT_PAREN = "RIGHT_PAREN"
    LEFT_SQUARE = "LEFT_SQUARE"
    RIGHT_SQUARE = "RIGHT_SQUARE"
    LEFT_BRACE = "LEFT_BRACE"
    RIGHT_BRACE = "RIGHT_BRACE"
    COMMA = "COMMA"
    PIPE = "PIPE"
    COLON = "COLON"
    DOT = "DOT"
    ARROW = "ARROW"
    EQUALS = "EQUALS"
