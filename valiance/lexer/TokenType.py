import enum


class TokenType(enum.Enum):
    NUMBER = "number"
    UNKNOWN = "unknown"
    STRING = "string"
    ELEMENT = "element"
    VARIABLE_GET = "variable_get"
    VARIABLE_SET = "variable_set"
    LIST_OPEN = "list_open"
    LIST_CLOSE = "list_close"
    FUNCTION_OPEN = "function_open"
    FUNCTION_CLOSE = "function_close"
    DICTIONARY_OPEN = "dictionary_open"
    COLON = "colon"
    COMMA = "comma"
    FUNCTION_RETURN_TYPE_SEPARATOR = "function_return_type_separator"
    FUNCTION_BODY_SEPARATOR = "function_body_separator"

    L_PAREN = "l_paren"
    R_PAREN = "r_paren"
    R_CURLY = "r_curly"

    NAME = "name"
    TYPE = "type"

    HASH_ELEMENT = "hash_element"
