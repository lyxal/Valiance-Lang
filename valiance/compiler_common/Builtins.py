from typing import Protocol
from compiler_common.Identifier import Identifier
from valiance.analyser.Symbol import DefineSymbol, Symbol
from vtypes.VTypes import *


class RegisterBuiltinFn(Protocol):
    def __call__(
        self,
        name: str,
        inputs: list[VType],
        outputs: list[VType],
        generics: list[VType] | None = ...,
    ) -> str: ...


class AliasFn(Protocol):
    def __call__(self, original: str, alias_name: str) -> str: ...


def make_empty_builtins() -> tuple[
    dict[str, Symbol],
    RegisterBuiltinFn,
    AliasFn,
]:
    register: dict[str, Symbol] = {}

    def register_builtin(
        name: str,
        inputs: list[VType],
        outputs: list[VType],
        generics: list[VType] | None = None,
    ) -> str:
        if generics is None:
            generics = []

        register[name] = DefineSymbol(
            generics=generics,
            element_tags=[],
            parameters=inputs,
            outputs=outputs,
        )
        return name

    def alias(original: str, alias_name: str) -> str:
        register[alias_name] = register[original]
        return alias_name

    return register, register_builtin, alias


def make_typevar(name: str) -> CustomType:
    return CustomType(Identifier(name=name), [], [])


BUILTINS, register_builtin, alias = make_empty_builtins()

# --- Mathematical built-in functions + some aliases

# a + b
ADD = register_builtin("add", [NumberType(), NumberType()], [NumberType()])
PLUS = alias("add", "plus")

# a - b
MINUS = register_builtin("minus", [NumberType(), NumberType()], [NumberType()])
SUB = alias("minus", "sub")

# a * b
MULTIPLY = register_builtin("multiply", [NumberType(), NumberType()], [NumberType()])
TIMES = alias("multiply", "times")

# a / b
DIV = register_builtin("div", [NumberType(), NumberType()], [NumberType()])
DIVIDE = alias("div", "divide")

# a % b
MOD = register_builtin("mod", [NumberType(), NumberType()], [NumberType()])
MODULO = alias("mod", "modulo")
REMAINDER = alias("mod", "remainder")

# a // b (floor division)
FLOOR_DIV = register_builtin("floor_div", [NumberType(), NumberType()], [NumberType()])
FLOOR_DIVIDE = alias("floor_div", "floor_divide")

# a ** b
POW = register_builtin("pow", [NumberType(), NumberType()], [NumberType()])
POWER = alias("pow", "power")

# --- List built-in functions

# len(lst)
LEN = register_builtin(
    "len",
    [ExactRankType(make_typevar("T"), 1)],
    [NumberType()],
    generics=[make_typevar("T")],
)
LENGTH = alias("len", "length")

# map(func, lst)

MAP = register_builtin(
    "map",
    [
        ExactRankType(make_typevar("T"), 1),
        FunctionType(
            True,
            [make_typevar("T"), make_typevar("U")],
            [make_typevar("T")],
            [make_typevar("U")],
            [],
        ),
    ],
    [ExactRankType(make_typevar("U"), 1)],
    generics=[make_typevar("T"), make_typevar("U")],
)

# --- Character aliases of built-in functions

SYM_ASTERISK = alias("multiply", "*")
SYM_DOUBLE_ASTERISK = alias("pow", "**")
SYM_DOUBLE_SLASH = alias("floor_div", "//")
SYM_HYPHEN = alias("minus", "-")
SYM_PERCENT = alias("mod", "%")
SYM_PLUS = alias("add", "+")
SYM_SLASH = alias("div", "/")
