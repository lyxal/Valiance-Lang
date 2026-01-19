from valiance.compiler_common.Identifier import Identifier
from valiance.vtypes.VTypes import NumberType, Overload, StringType, VType


PRIMITIVES: dict[Identifier, list[Overload]] = {}


def register_primitive(name: str, inputs: list[VType], outputs: list[VType]):
    ident = Identifier(name=name)
    if ident not in PRIMITIVES:
        PRIMITIVES[ident] = []
    overload = Overload(
        params=inputs,
        returns=outputs,
        arity=len(inputs),
        multiplicity=len(outputs),
    )
    PRIMITIVES[ident].append(overload)


def register_alias(original: str, *aliases: str):
    original_ident = Identifier(name=original)
    if original_ident not in PRIMITIVES:
        return
    for alias in aliases:
        alias_ident = Identifier(name=alias)
        PRIMITIVES[alias_ident] = PRIMITIVES[original_ident][::]


def register_alias_for_overload(target: str, types: list[VType], *aliases: str):
    target_ident = Identifier(name=target)
    if target_ident not in PRIMITIVES:
        return
    matching_overloads = [
        overload for overload in PRIMITIVES[target_ident] if overload.params == types
    ]
    for alias in aliases:
        alias_ident = Identifier(name=alias)
        if alias_ident not in PRIMITIVES:
            PRIMITIVES[alias_ident] = []
        PRIMITIVES[alias_ident].extend(matching_overloads)


register_primitive("+", [NumberType(), NumberType()], [NumberType()])
register_alias_for_overload("+", [NumberType(), NumberType()], "add", "sum")
register_primitive("+", [StringType(), StringType()], [StringType()])
register_alias_for_overload("+", [StringType(), StringType()], "concat")
register_primitive("-", [NumberType(), NumberType()], [NumberType()])
register_alias_for_overload(
    "-", [NumberType(), NumberType()], "subtract", "sub", "minus"
)
register_primitive("*", [NumberType(), NumberType()], [NumberType()])
register_alias_for_overload("*", [NumberType(), NumberType()], "multiply", "mul")
