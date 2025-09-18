import enum


class TokenType(enum.Enum):
    NUMBER = "number"
    UNKNOWN = "unknown"
    STRING = "string"
    TEMPLATE_STRING = "template_string"
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

    HASH_L_PAREN = "hash_l_paren"
    HASH_R_PAREN = "hash_r_paren"
    HASH_L_SQUARE = "hash_l_square"
    HASH_R_SQUARE = "hash_r_square"

    PIPE = "pipe"
    AT_SYMBOL = "at_symbol"

    HASH_ELEMENT = "hash_element"
