import enum


class AstType(enum.Enum):
    TYPE = "type"
    NUMBERIC_LITERAL = "numeric_literal"
    STRING_LITERAL = "string_literal"
    TEMPLATE_STRING_LITERAL = "template_string_literal"
    LIST_LITERAL = "list_literal"
    TUPLE_LITERAL = "tuple_literal"
    DICTIONARY_LITERAL = "dictionary_literal"

    ELEMENT = "element"
    VARIABLE_GET = "variable_get"
    VARIABLE_SET = "variable_set"
    GROUP = "group"
    FUNCTION = "function"
    GENERIC_TYPE = "generic_type"
