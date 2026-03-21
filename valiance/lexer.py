from enum import Enum, auto


class TokenType(Enum):
    # === Literals ===
    NUMBER = auto()  # any numeric literal: 69, -3.14, 69i420, 6e7, 1e2i3e4, …

    # String interpolation – a string is emitted as a sequence of these tokens:
    #   STRING_START  STRING_CONTENT?
    #   ( INTERP_START <tokens> INTERP_END STRING_CONTENT? )*
    #   STRING_END
    # A plain string with no interpolation still uses START/END so the parser
    # has a uniform shape.  STRING_CONTENT holds the raw (unescaped) text
    # between interpolations.  INTERP_START covers both "$ident" (the lexer
    # emits VARIABLE directly after it) and "${" (arbitrary tokens follow until
    # the matching INTERP_END / "}").
    STRING_START = auto()  # the opening "
    STRING_CONTENT = auto()  # literal text segment inside a string
    INTERP_START = auto()  # $ (before identifier) or ${ (before expression)
    INTERP_END = auto()  # implicit end-of-identifier or explicit }
    STRING_END = auto()  # the closing "

    # === Identifiers & references ===
    IDENTIFIER = auto()  # element / type names: foo, +, <=, myElement2
    VARIABLE = auto()  # $name
    TAG_NAME = auto()  # #sorted, #infinite, #boolean …

    # === Keywords ===
    # Declarations
    DEFINE = auto()  # define
    VECDEFINE = auto()  # vecdefine
    MULTI = auto()  # multi  (used before define)
    OBJECT = auto()  # object
    TRAIT = auto()  # trait
    VARIANT = auto()  # variant
    ENUM = auto()  # enum
    TAG = auto()  # tag  (tag declaration keyword)
    EXTERNAL = auto()  # external
    IMPORT = auto()  # import
    PUBLIC = auto()  # public
    CAST = auto()  # cast  (type-cast definition)

    # Access modifiers
    PRIVATE = auto()  # private
    READABLE = auto()  # readable

    # Block delimiters
    ARROW = auto()  # =>
    END = auto()  # end

    # Functions & closures
    FN = auto()  # fn
    RETURN_ARROW = auto()  # ->

    # Control flow
    IF = auto()  # if
    ELSE = auto()  # else
    WHILE = auto()  # while
    FOREACH = auto()  # foreach
    UNFOLD = auto()  # unfold
    AT = auto()  # at
    BREAK = auto()  # break
    MATCH = auto()  # match
    AS = auto()  # as  (type-cast / match arm)
    AS_BANG = auto()  # as!  (unsafe type-cast)
    DEFAULT = auto()  # default  (match fallthrough)
    TRY = auto()  # try
    HANDLE = auto()  # handle

    # Error / assertion
    ASSERT = auto()  # assert
    PANIC = auto()  # panic

    # Type-system keywords
    VEC = auto()  # vec  (vectorisation marker in params)
    ATOMIC = auto()  # atomic  (atomic generic marker)
    CONST = auto()  # const
    EXTEND = auto()  # extend  (trait required-impl / extend modifier)
    WHERE = auto()  # where  (where clause)
    SELF = auto()  # self

    # Literal aliases
    TRUE = auto()  # true  (alias for 1)
    FALSE = auto()  # false  (alias for 0)
    NONE = auto()  # None

    # === Modifiers (prefix sigils) ===
    COLON_MOD = auto()  # :  element modifier (wrap next elem as fn arg)
    BACKSLASH_MOD = auto()  # \  infix / right-hand-value modifier
    TICK = auto()  # '  quick-function wrapper  'element == fn => element
    AT_SIGN = auto()  # @  annotation prefix
    DOUBLE_AT = auto()  # @@ annotation prefix (return / invocation convention)

    # === Annotations (bare names after @ / @@) ===
    # These are represented as IDENTIFIER tokens preceded by AT_SIGN / DOUBLE_AT;
    # listed here for documentation only – no separate token needed in practice.

    # === Punctuation & delimiters ===
    L_PAREN = auto()  # (
    R_PAREN = auto()  # )
    L_BRACKET = auto()  # [
    R_BRACKET = auto()  # ]
    L_BRACE = auto()  # {  used in tuple types {T, U}
    R_BRACE = auto()  # }
    COMMA = auto()  # ,
    DOT = auto()  # .  member access  $.field  or  $name.field
    COLON = auto()  # :  type annotation  $name: Type
    DOUBLE_COLON = auto()  # :: object-friendly element access  Name::element
    SEMICOLON = auto()  # ;  statement separator (inside ECS / where clauses)
    TILDE = auto()  # ~  local-root import prefix  ~utils
    UNDERSCORE = auto()  # _  placeholder / wildcard

    # === Operators ===
    # Assignment
    ASSIGN = auto()  # =
    AUG_ASSIGN = auto()  # :=  augmented assignment

    # Note: +, *, ~ are NOT given dedicated rank-suffix tokens.  The lexer
    # always emits them as IDENTIFIER tokens; the parser decides from context
    # (e.g. following a type name) whether they are rank suffixes or operators.
    ELLIPSIS = auto()  # ...  variadic tuple type  {Number...}

    # Type operators
    PIPE = auto()  # |  union type
    AMPERSAND = auto()  # &  intersection type
    QUESTION = auto()  # ?  optional type suffix
    QUESTION_BANG = auto()  # ?!  unsafe unwrap element
    QUESTION_GT = auto()  # ?>  flatmap / and_then element

    # Hash / tag sigils
    HASH = auto()  # #  starts a tag application  #sorted
    HASH_BANG = auto()  # #! tag removal  #!sorted

    # Misc operators
    DOLLAR_BRACKET = auto()  # $[  stack-index / slice operator

    # === Comments ===
    LINE_COMMENT = auto()  # #?  …  (single-line comment)
    BLOCK_COMMENT = auto()  # #/ … /#  (nested multi-line comment)

    # === Special ===
    NEWLINE = auto()  # significant newline (ends statements / values)
    EOF = auto()  # end of file
    ERROR = auto()  # lexer error (e.g. unterminated string)


class Token:
    def __init__(
        self, type_: TokenType, value: str, start: int, end: int, line: int, column: int
    ):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column
        self.start = start
        self.end = end

    def __repr__(self):
        return f"Token(type={self.type}, value='{self.value}', line={self.line}, column={self.column})"
