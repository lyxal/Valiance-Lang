# type: ignore
from __future__ import annotations

from dataclasses import is_dataclass, fields
from pathlib import Path
from typing import Any, Iterable, Optional
import html
import shutil
import subprocess

from valiance.parser.AST import (
    ASTNode,
    AuxiliaryNode,
    AuxiliaryTokenNode,
    GroupNode,
    Parameter,
)
from valiance.compiler_common.Identifier import Identifier
from valiance.vtypes.VTypes import DataTag, ElementTag, NegateElementTag


# ---- dark theme ----
BG = "#0F1115"
FG = "#E6E6E6"
MUTED = "#B7BDC6"
NEUTRAL_BORDER = "#8A8F98"

TABLE_HDR_BG = "#141922"
TABLE_KEY_BG = "#1B2230"
TABLE_VAL_BG = "#121821"

# ---- config knobs ----
INLINE_AST_LIST_FIELD_NAMES = {
    "arguments",
    "args",
    "modifier_args",
    "items",
    "elements",
    "branches",
    "entries",
    "variants",
    "required_methods",
    "default_methods",
    "variant_objects",
    "fields",
    "members",
    "methods",
    "parent_traits",
    "default_constructor",
    # control flow payloads
    "values",  # BreakNode(values)
    # tags
    "rules",
}
MAX_INLINE_LIST_ITEMS = 6
MAX_INLINE_STRING = 60

GROUP_LIST_FIELDS = {
    "args",
    "modifier_args",
    "required_methods",
    "default_methods",
    "variant_objects",
    "fields",
    "members",
    "methods",
    "parent_traits",
    "variants",
    "branches",
    "entries",
    "items",
    "elements",
    "default_constructor",
    # control flow payloads
    "values",  # BreakNode(values)
    # tags
    "rules",
}
MAX_EDGES_PER_GROUP = 12

# keep the diagram readable
LABEL_NON_FLOW_EDGES = False


def _html_escape(s: str) -> str:
    return html.escape(s, quote=True)


def _ident_to_str(ident: Any) -> str:
    return str(ident) if isinstance(ident, Identifier) else str(ident)


def _skip_node(node: ASTNode) -> bool:
    return isinstance(node, (AuxiliaryNode, AuxiliaryTokenNode))


def _short(s: str, n: int = MAX_INLINE_STRING) -> str:
    s = s.replace("\n", "\\n")
    return s if len(s) <= n else s[: n - 1] + "…"


def _pretty_scalar(val: Any) -> str:
    """
    Pretty-printer for non-AST scalar-ish values.

    NOTE: Your VType.toString() does NOT include tags.
    Your VType.formatthis() DOES include tags, so prefer it when present.
    """
    if val is None:
        return ""

    fmt = getattr(val, "formatthis", None)
    if callable(fmt):
        try:
            s = str(fmt())
            if s:
                return _short(s)
        except Exception:
            pass

    to_string = getattr(val, "toString", None)
    if callable(to_string):
        try:
            s = str(to_string())
            if s:
                return _short(s)
        except Exception:
            pass

    enum_value = getattr(val, "value", None)
    if isinstance(enum_value, str):
        return _short(enum_value)

    if isinstance(val, ElementTag):
        return _short("+ " + val.name.name)
    if isinstance(val, NegateElementTag):
        return _short("- " + val.name.name)
    if isinstance(val, DataTag):
        return _short("#" + val.name.name + f" (depth={val.depth})")

    if isinstance(val, Identifier):
        return _short(_ident_to_str(val))
    if isinstance(val, str):
        return _short(val)
    if isinstance(val, (int, float, bool)):
        return str(val)

    return _short(str(val))


# -------- OverlayRule support (non-dataclass) --------


def _is_overlay_rule(obj: Any) -> bool:
    # class OverlayRule: element: Identifier, generics: list[VType], arguments: list[VType], returns: list[VType]
    return (
        obj is not None
        and not is_dataclass(obj)
        and type(obj).__name__ == "OverlayRule"
        and isinstance(getattr(obj, "element", None), Identifier)
    )


def _overlay_rule_parts(r: Any) -> tuple[str, str, str]:
    element = _ident_to_str(getattr(r, "element", "<element>"))
    generics = getattr(r, "generics", None) or []
    arguments = getattr(r, "arguments", None) or []
    returns = getattr(r, "returns", None) or []

    g = ""
    if generics:
        g = "[" + ", ".join(_pretty_scalar(t) for t in generics) + "] "

    # IMPORTANT: _pretty_scalar now prefers VType.formatthis(), so tags show here.
    inputs = g + "(" + ", ".join(_pretty_scalar(t) for t in arguments) + ")"
    outputs = ", ".join(_pretty_scalar(t) for t in returns)
    return (element, inputs, outputs)


def _overlay_rule_table_label(r: Any) -> str:
    # 3-column mini table: Element | Inputs | Outputs
    element, inputs, outputs = _overlay_rule_parts(r)
    header = "OverlayRule"
    return (
        "<"
        "<TABLE BORDER='1' CELLBORDER='1' CELLSPACING='0' CELLPADDING='6'>"
        f"<TR><TD COLSPAN='3' BGCOLOR='{TABLE_HDR_BG}' ALIGN='LEFT'><B>{_html_escape(header)}</B></TD></TR>"
        f"<TR>"
        f"<TD ALIGN='LEFT' BGCOLOR='{TABLE_KEY_BG}'><B>Element</B></TD>"
        f"<TD ALIGN='LEFT' BGCOLOR='{TABLE_KEY_BG}'><B>Inputs</B></TD>"
        f"<TD ALIGN='LEFT' BGCOLOR='{TABLE_KEY_BG}'><B>Outputs</B></TD>"
        f"</TR>"
        f"<TR>"
        f"<TD ALIGN='LEFT' BGCOLOR='{TABLE_VAL_BG}'>{_html_escape(element)}</TD>"
        f"<TD ALIGN='LEFT' BGCOLOR='{TABLE_VAL_BG}'>{_html_escape(inputs)}</TD>"
        f"<TD ALIGN='LEFT' BGCOLOR='{TABLE_VAL_BG}'>{_html_escape(outputs)}</TD>"
        f"</TR>"
        "</TABLE>"
        ">"
    )


def _overlay_rule_inline_sig(r: Any) -> str:
    element, inputs, outputs = _overlay_rule_parts(r)
    return f"{element}: {inputs} -> {outputs}"


# -------- MatchBranch + MatchPattern support --------


def _is_match_branch(obj: Any) -> bool:
    if obj is None or is_dataclass(obj):
        return False
    tn = type(obj).__name__
    if not (tn.startswith("Match") and tn.endswith("Branch")):
        return False
    # parser sets body for all cases
    return isinstance(getattr(obj, "body", None), ASTNode)


def _is_match_pattern(obj: Any) -> bool:
    return (
        obj is not None and is_dataclass(obj) and type(obj).__name__.endswith("Pattern")
    )


def _vtype_str(v: Any) -> str:
    s = _pretty_scalar(v)
    return s if s else ("" if v is None else str(v))


def _pattern_label(pat: Any) -> str:
    tn = type(pat).__name__
    if tn == "StringPattern":
        return "string"
    if tn == "ListPattern":
        elems = getattr(pat, "elements", None)
        n = len(elems) if elems is not None else 0
        return f"list[{n}]"
    if tn == "TuplePattern":
        elems = getattr(pat, "elements", None)
        n = len(elems) if elems is not None else 0
        return f"tuple[{n}]"
    if tn == "ErrorPattern":
        return "error"
    return tn.removesuffix("Pattern").lower() or tn


def _pattern_component_label(comp: Any) -> str:
    tn = type(comp).__name__
    if tn == "ASTComponent":
        node = getattr(comp, "node", None)
        if isinstance(node, ASTNode):
            return _ast_signature(node)
        return "ast"
    if tn == "WildcardComponent":
        name = getattr(comp, "name", None)
        return f"*{_ident_to_str(name)}" if isinstance(name, Identifier) else "*"
    if tn == "GreedyComponent":
        name = getattr(comp, "name", None)
        return f"...{_ident_to_str(name)}" if isinstance(name, Identifier) else "..."
    return tn.removesuffix("Component")


def _iter_match_pattern_children(
    prefix: str, pat: Any
) -> Iterable[tuple[str, ASTNode]]:
    tn = type(pat).__name__

    if tn == "StringPattern":
        v = getattr(pat, "value", None)
        if isinstance(v, ASTNode):
            yield (f"{prefix}.value", v)
        return

    if tn in ("ListPattern", "TuplePattern"):
        elems = getattr(pat, "elements", None)
        if elems is None:
            return
        for i, comp in enumerate(elems):
            if type(comp).__name__ == "ASTComponent":
                node = getattr(comp, "node", None)
                if isinstance(node, ASTNode):
                    yield (
                        f"{prefix}.elements[{i}] {_pattern_component_label(comp)}",
                        node,
                    )
        return


def _match_branch_label(branch: Any) -> str:
    tn = type(branch).__name__
    has_pred = isinstance(getattr(branch, "predicate", None), ASTNode)

    if tn == "MatchExactBranch":
        vals = getattr(branch, "values", None)
        n = len(vals) if isinstance(vals, list) else 0
        return f"exact[{n}]"

    if tn == "MatchIfBranch":
        return "if"

    if tn == "MatchPatternBranch":
        pat = getattr(branch, "pattern", None)
        inner = _pattern_label(pat) if _is_match_pattern(pat) else "pattern"
        return f"{inner}?" if has_pred else inner

    if tn == "MatchAsBranch":
        name = getattr(branch, "name", None)
        type_ = getattr(branch, "type_", None)

        name_s = _ident_to_str(name) if isinstance(name, Identifier) else ""
        type_s = _vtype_str(type_) if type_ is not None else ""

        if name_s and type_s:
            inner = f"{name_s}: {type_s}"
        elif name_s:
            inner = name_s
        elif type_s:
            inner = type_s
        else:
            inner = "as"

        return f"as({inner})" + ("?" if has_pred else "")

    if tn == "MatchDefaultBranch":
        return "default"

    return tn.removesuffix("Branch").removeprefix("Match").lower() or tn


def _iter_match_branch_children(
    prefix: str, branch: Any
) -> Iterable[tuple[str, ASTNode]]:
    tn = type(branch).__name__

    if tn == "MatchExactBranch":
        values = getattr(branch, "values", None)
        if isinstance(values, list):
            for i, v in enumerate(values):
                if isinstance(v, ASTNode):
                    yield (f"{prefix}.values[{i}]", v)

    elif tn == "MatchIfBranch":
        cond = getattr(branch, "condition", None)
        if isinstance(cond, ASTNode):
            yield (f"{prefix}.condition", cond)

    elif tn == "MatchPatternBranch":
        pat = getattr(branch, "pattern", None)
        if _is_match_pattern(pat):
            yield from _iter_match_pattern_children(
                f"{prefix}.pat({_pattern_label(pat)})", pat
            )
        pred = getattr(branch, "predicate", None)
        if isinstance(pred, ASTNode):
            yield (f"{prefix}.predicate", pred)

    elif tn == "MatchAsBranch":
        pred = getattr(branch, "predicate", None)
        if isinstance(pred, ASTNode):
            yield (f"{prefix}.predicate", pred)

    body = getattr(branch, "body", None)
    if isinstance(body, ASTNode):
        yield (f"{prefix}.body", body)


# -------- other formatting / signature --------


def _trait_impl_trait_label(node: ASTNode) -> Optional[str]:
    if type(node).__name__ != "TraitImplTraitNode":
        return None
    if not is_dataclass(node):
        return None

    trait_name = getattr(node, "trait_name", None)
    parent_trait = getattr(node, "parent_trait", None)

    if not isinstance(trait_name, Identifier):
        return None
    parent_s = _pretty_scalar(parent_trait)
    if parent_s:
        return f"{_ident_to_str(trait_name)} : {parent_s}"
    return _ident_to_str(trait_name)


def _ast_signature(node: ASTNode) -> str:
    if isinstance(node, GroupNode):
        try:
            return f"Group({len(node.elements)})"
        except Exception:
            return "Group"

    cls = type(node).__name__.removesuffix("Node")

    if is_dataclass(node):
        if hasattr(node, "value"):
            v = getattr(node, "value", None)
            if not isinstance(v, ASTNode):
                return f"{cls}({_pretty_scalar(v)})"

        impl_lbl = _trait_impl_trait_label(node)
        if impl_lbl is not None:
            return f"{cls}({impl_lbl})"

        if hasattr(node, "name"):
            nm = getattr(node, "name", None)
            if isinstance(nm, Identifier):
                return f"{cls}({_ident_to_str(nm)})"
            if isinstance(nm, str) and nm:
                return f"{cls}({nm})"

        if hasattr(node, "trait_name"):
            tn = getattr(node, "trait_name", None)
            if isinstance(tn, Identifier):
                return f"{cls}({_ident_to_str(tn)})"

        if hasattr(node, "element_name"):
            en = getattr(node, "element_name", None)
            if isinstance(en, Identifier):
                return f"{cls}({_ident_to_str(en)})"
            if isinstance(en, str) and en:
                return f"{cls}({en})"

        if hasattr(node, "object_name"):
            on = getattr(node, "object_name", None)
            if isinstance(on, Identifier):
                return f"{cls}({_ident_to_str(on)})"

    return cls


def _is_named_ast_pair(x: Any) -> bool:
    return (
        isinstance(x, tuple)
        and len(x) == 2
        and isinstance(x[0], Identifier)
        and isinstance(x[1], ASTNode)
    )


def _is_param_default_pair(x: Any) -> bool:
    return (
        isinstance(x, tuple)
        and len(x) == 2
        and isinstance(x[0], Parameter)
        and (x[1] is None or isinstance(x[1], ASTNode))
    )


def _is_field_default_pair(x: Any) -> bool:
    return (
        isinstance(x, tuple)
        and len(x) == 2
        and isinstance(x[0], ASTNode)
        and type(x[0]).__name__ == "FieldNode"
        and (x[1] is None or isinstance(x[1], ASTNode))
    )


def _param_sig(p: Parameter) -> str:
    name = _ident_to_str(getattr(p, "name", "<anon>"))
    type_s = _pretty_scalar(getattr(p, "type_", None))
    cast = getattr(p, "cast", None)

    s = f"{name}"
    if type_s:
        s += f": {type_s}"
    if cast is not None:
        s += f" as {_pretty_scalar(cast)}"
    return s


def _field_sig(field_node: Any) -> str:
    vis = getattr(field_node, "visibility", None)
    vis_s = _pretty_scalar(vis) if vis is not None else ""

    name = _ident_to_str(getattr(field_node, "name", "<field>"))
    type_s = _pretty_scalar(getattr(field_node, "type_", None))

    left = f"{vis_s} {name}".strip()
    return f"{left}: {type_s}" if type_s else left


def _member_sig(member_node: Any) -> str:
    vis = getattr(member_node, "visibility", None)
    vis_s = _pretty_scalar(vis) if vis is not None else ""
    name = _ident_to_str(getattr(member_node, "name", "<member>"))
    return f"{vis_s} {name}".strip()


def _summarize_named_ast_pairs(pairs: list[tuple[Identifier, ASTNode]]) -> str:
    items: list[str] = []
    for k, v in pairs[:MAX_INLINE_LIST_ITEMS]:
        items.append(f"{_ident_to_str(k)} = {_ast_signature(v)}")

    more = len(pairs) - len(items)
    bullet_lines = [f"• {_html_escape(s)}" for s in items]
    if more > 0:
        bullet_lines.append(f"• … (+{more} more)")
    return "<BR ALIGN='LEFT'/>".join(bullet_lines)


def _summarize_param_default_pairs(
    pairs: list[tuple[Parameter, Optional[ASTNode]]],
) -> str:
    items: list[str] = []
    for p, default in pairs[:MAX_INLINE_LIST_ITEMS]:
        if default is None:
            items.append(_param_sig(p))
        else:
            items.append(f"{_param_sig(p)} = {_ast_signature(default)}")

    more = len(pairs) - len(items)
    bullet_lines = [f"• {_html_escape(s)}" for s in items]
    if more > 0:
        bullet_lines.append(f"• … (+{more} more)")
    return "<BR ALIGN='LEFT'/>".join(bullet_lines)


def _summarize_field_default_pairs(pairs: list[tuple[Any, Optional[ASTNode]]]) -> str:
    items: list[str] = []
    for fld, default in pairs[:MAX_INLINE_LIST_ITEMS]:
        if default is None:
            items.append(_field_sig(fld))
        else:
            items.append(f"{_field_sig(fld)} = {_ast_signature(default)}")

    more = len(pairs) - len(items)
    bullet_lines = [f"• {_html_escape(s)}" for s in items]
    if more > 0:
        bullet_lines.append(f"• … (+{more} more)")
    return "<BR ALIGN='LEFT'/>".join(bullet_lines)


def _summarize_sequence(seq: list[Any]) -> str:
    if seq and all(_is_named_ast_pair(x) for x in seq):
        return _summarize_named_ast_pairs(seq)  # type: ignore[arg-type]
    if seq and all(_is_param_default_pair(x) for x in seq):
        return _summarize_param_default_pairs(seq)  # type: ignore[arg-type]
    if seq and all(_is_field_default_pair(x) for x in seq):
        return _summarize_field_default_pairs(seq)  # type: ignore[arg-type]

    if seq and all(_is_match_branch(x) for x in seq):
        items = [
            f"• {_html_escape(_match_branch_label(b))}"
            for b in seq[:MAX_INLINE_LIST_ITEMS]
        ]
        more = len(seq) - min(len(seq), MAX_INLINE_LIST_ITEMS)
        if more > 0:
            items.append(f"• … (+{more} more)")
        return "<BR ALIGN='LEFT'/>".join(items)

    if seq and all(_is_overlay_rule(x) for x in seq):
        items = [
            f"• {_html_escape(_overlay_rule_inline_sig(r))}"
            for r in seq[:MAX_INLINE_LIST_ITEMS]
        ]
        more = len(seq) - min(len(seq), MAX_INLINE_LIST_ITEMS)
        if more > 0:
            items.append(f"• … (+{more} more)")
        return "<BR ALIGN='LEFT'/>".join(items)

    items: list[str] = []
    for x in seq[:MAX_INLINE_LIST_ITEMS]:
        if isinstance(x, ASTNode):
            tn = type(x).__name__
            if tn == "FieldNode":
                items.append(_field_sig(x))
            elif tn == "MemberNode":
                items.append(_member_sig(x))
            else:
                items.append(_ast_signature(x))
        elif _is_match_branch(x):
            items.append(_match_branch_label(x))
        elif _is_overlay_rule(x):
            items.append(_overlay_rule_inline_sig(x))
        elif _is_named_ast_pair(x):
            k, v = x
            items.append(f"{_ident_to_str(k)} = {_ast_signature(v)}")
        elif _is_param_default_pair(x):
            p, d = x
            items.append(
                _param_sig(p) if d is None else f"{_param_sig(p)} = {_ast_signature(d)}"
            )
        elif _is_field_default_pair(x):
            f, d = x
            items.append(
                _field_sig(f) if d is None else f"{_field_sig(f)} = {_ast_signature(d)}"
            )
        else:
            items.append(_pretty_scalar(x))

    more = len(seq) - len(items)
    bullet_lines = [f"• {_html_escape(s)}" for s in items]
    if more > 0:
        bullet_lines.append(f"• … (+{more} more)")
    return "<BR ALIGN='LEFT'/>".join(bullet_lines)


def _iter_ast_children(field_name: str, value: Any) -> Iterable[tuple[str, ASTNode]]:
    if value is None:
        return
    if isinstance(value, ASTNode):
        yield (field_name, value)
        return

    # OverlayRule contains no AST children (only VType/Identifier), so nothing to yield.
    # We render it as its own node via a special-case in walk().

    if _is_match_branch(value):
        yield from _iter_match_branch_children(field_name, value)
        return

    if isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            if isinstance(item, ASTNode):
                yield (f"{field_name}[{i}]", item)
            elif _is_match_branch(item):
                yield from _iter_match_branch_children(
                    f"{field_name}[{i}] {_match_branch_label(item)}", item
                )
            elif isinstance(item, tuple) and len(item) == 2:
                a, b = item
                if isinstance(a, Identifier) and isinstance(b, ASTNode):
                    yield (f"{field_name}[{i}] {_ident_to_str(a)}=", b)
                elif isinstance(a, ASTNode) and isinstance(b, ASTNode):
                    yield (f"{field_name}[{i}].0", a)
                    yield (f"{field_name}[{i}].1", b)
                elif isinstance(a, Parameter) and (b is None or isinstance(b, ASTNode)):
                    if isinstance(b, ASTNode):
                        yield (f"{field_name}[{i}] {_param_sig(a)}.default", b)
                elif (
                    isinstance(a, ASTNode)
                    and type(a).__name__ == "FieldNode"
                    and (b is None or isinstance(b, ASTNode))
                ):
                    if isinstance(b, ASTNode):
                        yield (f"{field_name}[{i}] {_field_sig(a)}.default", b)


def _has_ast_children(node: ASTNode) -> bool:
    if isinstance(node, GroupNode):
        return True
    if not is_dataclass(node):
        return False
    for f in fields(node):
        if f.name == "location":
            continue
        v = getattr(node, f.name, None)
        if isinstance(v, ASTNode):
            return True
        if _is_match_branch(v):
            return True
        if isinstance(v, (list, tuple)):
            for item in v:
                if isinstance(item, ASTNode):
                    return True
                if _is_match_branch(item):
                    return True
                if _is_named_ast_pair(item):
                    return True
                if _is_param_default_pair(item) and item[1] is not None:
                    return True
                if _is_field_default_pair(item) and item[1] is not None:
                    return True
                if (
                    isinstance(item, tuple)
                    and len(item) == 2
                    and any(isinstance(x, ASTNode) for x in item)
                ):
                    return True
    return False


def _has_direct_astnode_field(node: ASTNode) -> bool:
    if not is_dataclass(node):
        return False
    for f in fields(node):
        if f.name == "location":
            continue
        v = getattr(node, f.name, None)
        if isinstance(v, ASTNode):
            return True
    return False


def _is_forced_exit_scope(node: ASTNode) -> bool:
    # Make these nodes colored + have EXIT markers
    return type(node).__name__ in {
        "ObjectDefinitionNode",
        "ObjectTraitImplNode",
        "TraitNode",
        "TraitImplTraitNode",
        "MatchNode",
        "AssertNode",
        "AssertElseNode",
        "BreakNode",
        "TagCreationNode",
        "TagExtendNode",
        "TagDisjointNode",
    }


def _has_exit(node: ASTNode) -> bool:
    return _has_direct_astnode_field(node) or _is_forced_exit_scope(node)


def _needs_forced_exit(node: ASTNode) -> bool:
    return _is_forced_exit_scope(node)


def _param_to_line(p: Parameter) -> str:
    default = getattr(p, "default", None)
    s = _param_sig(p)
    if default is not None:
        s += " = <default>"
    return s


def _container_table_label(node: ASTNode) -> str:
    header = _html_escape(type(node).__name__)
    rows: list[tuple[str, str]] = []

    if is_dataclass(node):
        for f in fields(node):
            name = f.name
            if name == "location":
                continue

            v = getattr(node, name, None)
            if v is None:
                continue

            if (
                name == "parameters"
                and isinstance(v, list)
                and (not v or isinstance(v[0], Parameter))
            ):
                items = [_param_to_line(p) for p in v]
                cell = (
                    "<BR ALIGN='LEFT'/>".join(
                        f"• {_html_escape(line)}" for line in items
                    )
                    if items
                    else ""
                )
                rows.append((name.capitalize(), cell))
                continue

            if name == "element_tags" and isinstance(v, list):
                rows.append(
                    (
                        name.capitalize(),
                        _html_escape(" + ".join(_pretty_scalar(t) for t in v)),
                    )
                )
                continue

            # Inline summaries for AST-ish lists and OverlayRule lists
            if isinstance(v, (list, tuple)):
                if v and all(_is_overlay_rule(x) for x in v):
                    rows.append((name.capitalize(), _summarize_sequence(list(v))))
                    continue

            if isinstance(v, (list, tuple)) and any(
                isinstance(x, ASTNode)
                or _is_match_branch(x)
                or _is_named_ast_pair(x)
                or _is_param_default_pair(x)
                or _is_field_default_pair(x)
                for x in v
            ):
                if name in INLINE_AST_LIST_FIELD_NAMES:
                    rows.append((name.capitalize(), _summarize_sequence(list(v))))
                continue

            if isinstance(v, ASTNode) or isinstance(v, GroupNode):
                continue

            if isinstance(v, (list, tuple)):
                rows.append((name.capitalize(), _summarize_sequence(list(v))))
            else:
                rows.append((name.capitalize(), _html_escape(_pretty_scalar(v))))

    tr_rows = []
    for k, v in rows:
        tr_rows.append(
            "<TR>"
            f"<TD ALIGN='LEFT' BGCOLOR='{TABLE_KEY_BG}'><B>{_html_escape(k)}</B></TD>"
            f"<TD ALIGN='LEFT' BGCOLOR='{TABLE_VAL_BG}'>{v}</TD>"
            "</TR>"
        )

    return (
        "<"
        "<TABLE BORDER='1' CELLBORDER='1' CELLSPACING='0' CELLPADDING='6'>"
        f"<TR><TD COLSPAN='2' BGCOLOR='{TABLE_HDR_BG}' ALIGN='LEFT'><B>{header}</B></TD></TR>"
        + "".join(tr_rows)
        + "</TABLE>"
        ">"
    )


def _simple_box_label(node: ASTNode) -> str:
    parts = [type(node).__name__]

    if is_dataclass(node):
        tn = type(node).__name__
        if tn == "FieldNode":
            parts.append(_field_sig(node))
            return "\\n".join(_html_escape(p) for p in parts)
        if tn == "MemberNode":
            parts.append(_member_sig(node))
            return "\\n".join(_html_escape(p) for p in parts)

        for f in fields(node):
            if f.name in ("location",):
                continue
            v = getattr(node, f.name, None)
            if v is None:
                continue
            if isinstance(v, (ASTNode, GroupNode)):
                continue

            if isinstance(v, (list, tuple)):
                if all(isinstance(x, str) for x in v):
                    parts.append(f"{f.name}=[{','.join(v)}]")
                continue

            if isinstance(v, Identifier):
                parts.append(f"{f.name}={_ident_to_str(v)}")
            elif isinstance(v, (str, int, float, bool)):
                parts.append(f"{f.name}={v}")
            else:
                to_string = getattr(v, "toString", None)
                if callable(to_string):
                    parts.append(f"{f.name}={_pretty_scalar(v)}")

    return "\\n".join(_html_escape(p) for p in parts)


def _exit_display_name(node: ASTNode) -> str:
    impl_lbl = _trait_impl_trait_label(node)
    if impl_lbl is not None:
        return f"{type(node).__name__}({impl_lbl})"

    if is_dataclass(node) and hasattr(node, "object_name"):
        on = getattr(node, "object_name", None)
        if isinstance(on, Identifier):
            return f"{type(node).__name__}({_ident_to_str(on)})"

    if is_dataclass(node) and hasattr(node, "trait_name"):
        tn = getattr(node, "trait_name", None)
        if isinstance(tn, Identifier):
            return f"{type(node).__name__}({_ident_to_str(tn)})"

    if is_dataclass(node) and hasattr(node, "name"):
        nm = getattr(node, "name", None)
        if isinstance(nm, Identifier):
            return f"{type(node).__name__}({_ident_to_str(nm)})"
        if isinstance(nm, str) and nm:
            return f"{type(node).__name__}({nm})"
    return type(node).__name__


def ast_to_dot(root: ASTNode, *, rankdir: str = "TB") -> str:
    node_ids: dict[int, str] = {}
    out_nodes: list[str] = []
    out_edges: list[str] = []
    exit_ids: dict[str, str] = {}
    entry_color: dict[str, str] = {}
    color_i = 0
    anon_i = 0

    palette = [
        "#1F77B4",
        "#E74C3C",
        "#2ECC71",
        "#F1C40F",
        "#9B59B6",
        "#16A085",
        "#E67E22",
        "#00BCD4",
        "#FF00FF",
        "#7FFF00",
        "#0B3C5D",
        "#641E16",
        "#145A32",
        "#7D6608",
        "#4A235A",
        "#0E6251",
        "#784212",
        "#1B2631",
    ]

    out_nodes.append(
        f'root [shape=box, style="rounded", color="{NEUTRAL_BORDER}", fontcolor="{FG}", label="ROOT"];'
    )

    def gen_new_colour() -> str:
        nonlocal color_i
        c = palette[color_i % len(palette)]
        color_i += 1
        return c

    def nid(node: ASTNode) -> str:
        k = id(node)
        if k not in node_ids:
            node_ids[k] = f"n{len(node_ids)}"
        return node_ids[k]

    def new_anon(prefix: str) -> str:
        nonlocal anon_i
        anon_i += 1
        return f"{prefix}_{anon_i}"

    def get_or_assign_structure_color(entry_id: str) -> str:
        if entry_id not in entry_color:
            entry_color[entry_id] = gen_new_colour()
        return entry_color[entry_id]

    def emit(node: ASTNode, *, node_color: str, penwidth: int) -> str:
        n = nid(node)
        if _has_ast_children(node) and not isinstance(node, GroupNode):
            out_nodes.append(
                f'{n} [shape=plain, color="{node_color}", penwidth={penwidth}, fontcolor="{FG}", label={_container_table_label(node)}];'
            )
        else:
            out_nodes.append(
                f'{n} [shape=box, color="{node_color}", penwidth={penwidth}, fontcolor="{FG}", label="{_simple_box_label(node)}"];'
            )
        return n

    def emit_folder(*, title: str, count: int, node_color: str) -> str:
        fid = new_anon("fld")
        out_nodes.append(
            f'{fid} [shape=box, style="rounded", penwidth=1, color="{node_color}", fontcolor="{FG}", label="{_html_escape(title)} ({count})"];'
        )
        return fid

    def emit_more(*, hidden_count: int, node_color: str) -> str:
        mid = new_anon("more")
        out_nodes.append(
            f'{mid} [shape=box, style="rounded,dashed", penwidth=1, color="{node_color}", fontcolor="{MUTED}", '
            f'label="{_html_escape("… (+" + str(hidden_count) + " more)")}"];'
        )
        return mid

    def emit_branch_hub(*, text: str, node_color: str) -> str:
        bid = new_anon("br")
        out_nodes.append(
            f'{bid} [shape=box, style="rounded", penwidth=1, color="{node_color}", fontcolor="{FG}", label="{_html_escape(text)}"];'
        )
        return bid

    def emit_small_hub(*, text: str, node_color: str) -> str:
        hid = new_anon("hub")
        out_nodes.append(
            f'{hid} [shape=box, style="rounded", penwidth=1, color="{node_color}", fontcolor="{FG}", label="{_html_escape(text)}"];'
        )
        return hid

    def emit_overlay_rule(r: Any, *, node_color: str, penwidth: int = 1) -> str:
        rid = new_anon("rule")
        out_nodes.append(
            f'{rid} [shape=plain, color="{node_color}", penwidth={penwidth}, fontcolor="{FG}", label={_overlay_rule_table_label(r)}];'
        )
        return rid

    def link(
        a: str,
        b: str,
        label: str,
        *,
        color: Optional[str] = None,
        show_label: bool = True,
        weight: Optional[int] = None,
        style: Optional[str] = None,
        arrowhead: Optional[str] = None,
    ) -> None:
        c = color or MUTED
        w = f", weight={weight}" if weight is not None else ""
        st = f', style="{style}"' if style else ""
        ah = f', arrowhead="{arrowhead}"' if arrowhead else ""

        if show_label and label:
            out_edges.append(
                f'{a} -> {b} [label="{_html_escape(label)}", color="{c}", fontcolor="{c}"{w}{st}{ah}];'
            )
        else:
            out_edges.append(f'{a} -> {b} [color="{c}"{w}{st}{ah}];')

    def link_dotted(a: str, b: str, *, color: str) -> None:
        out_edges.append(f'{a} -> {b} [style=dotted, color="{color}", arrowhead=none];')

    def emit_exit_marker(entry_id: str, node: ASTNode, *, color: str) -> str:
        if entry_id in exit_ids:
            return exit_ids[entry_id]
        eid = f"{entry_id}_exit"
        exit_ids[entry_id] = eid
        who = _exit_display_name(node)
        out_nodes.append(
            f'{eid} [shape=box, style="rounded,dashed", penwidth=2, color="{color}", fontcolor="{color}", '
            f'label="{_html_escape("EXIT " + who)}"];'
        )
        link_dotted(entry_id, eid, color=color)
        return eid

    def walk(
        node: ASTNode, inherited_color: Optional[str]
    ) -> tuple[Optional[str], Optional[str]]:
        if _skip_node(node):
            return (None, None)

        if isinstance(node, GroupNode):
            first_entry: Optional[str] = None
            prev_exit: Optional[str] = None
            for child in node.elements:
                c_entry, c_exit = walk(child, inherited_color)
                if c_entry is None or c_exit is None:
                    continue
                if first_entry is None:
                    first_entry = c_entry
                if prev_exit is not None:
                    link(prev_exit, c_entry, "next", color=inherited_color, weight=5)
                prev_exit = c_exit
            return (first_entry, prev_exit)

        structure_color: Optional[str] = None
        if _has_exit(node):
            structure_color = get_or_assign_structure_color(nid(node))

        node_color = structure_color or inherited_color or NEUTRAL_BORDER
        penwidth = 2 if structure_color else 1

        entry = emit(node, node_color=node_color, penwidth=penwidth)
        exit_ = entry

        if is_dataclass(node) and hasattr(node, "parameters"):
            params = getattr(node, "parameters", None)
            if isinstance(params, list) and (
                not params or isinstance(params[0], Parameter)
            ):
                for i, p in enumerate(params):
                    d = getattr(p, "default", None)
                    if isinstance(d, ASTNode) and not _skip_node(d):
                        d_entry, _ = walk(d, node_color)
                        if d_entry is not None:
                            link(
                                entry,
                                d_entry,
                                f"parameters[{i}].default",
                                color=node_color,
                            )

        if is_dataclass(node):
            for f in fields(node):
                if f.name == "location":
                    continue
                if f.name == "parameters" and hasattr(node, "parameters"):
                    continue

                v = getattr(node, f.name, None)
                if v is None:
                    continue

                # --- TagCreation/TagExtend rules (OverlayRule list) ---
                if (
                    type(node).__name__ in {"TagCreationNode", "TagExtendNode"}
                    and f.name == "rules"
                ):
                    if (
                        isinstance(v, list)
                        and v
                        and all(_is_overlay_rule(x) for x in v)
                    ):
                        folder = emit_folder(
                            title="rules", count=len(v), node_color=node_color
                        )
                        link(entry, folder, "rules", color=node_color)

                        shown_rules = v[:MAX_EDGES_PER_GROUP]
                        for r in shown_rules:
                            rn = emit_overlay_rule(r, node_color=node_color, penwidth=1)
                            link(folder, rn, "", color=node_color, show_label=False)

                        hidden = len(v) - len(shown_rules)
                        if hidden > 0:
                            more = emit_more(hidden_count=hidden, node_color=node_color)
                            link(folder, more, "more", color=node_color)
                        continue

                # --- Assert/AssertElse: make cond/else explicit even when they are GroupNodes ---
                if (
                    type(node).__name__ in {"AssertNode", "AssertElseNode"}
                    and f.name == "condition"
                ):
                    if isinstance(v, GroupNode):
                        hub = emit_small_hub(text="cond", node_color=node_color)
                        link(
                            entry,
                            hub,
                            "cond",
                            color=node_color,
                            show_label=True,
                            weight=3,
                        )

                        c_entry, c_exit = walk(v, node_color)
                        if c_entry is not None:
                            link(
                                hub,
                                c_entry,
                                "",
                                color=node_color,
                                show_label=False,
                                weight=3,
                            )
                        if c_exit is not None:
                            exit_ = c_exit
                        continue

                if type(node).__name__ == "AssertElseNode" and f.name == "else_branch":
                    if isinstance(v, GroupNode):
                        hub = emit_small_hub(text="else", node_color=node_color)
                        link(
                            entry,
                            hub,
                            "else",
                            color=node_color,
                            show_label=True,
                            style="dashed",
                            weight=2,
                        )

                        e_entry, _e_exit = walk(v, node_color)
                        if e_entry is not None:
                            link(
                                hub,
                                e_entry,
                                "",
                                color=node_color,
                                show_label=False,
                                style="dashed",
                                weight=2,
                            )
                        # don't set exit_ from else_branch (else isn't the linear continuation)
                        continue

                # --- MatchNode.branches: per-branch hub + local spine ---
                if (
                    f.name == "branches"
                    and isinstance(v, list)
                    and v
                    and all(_is_match_branch(x) for x in v)
                ):
                    folder = emit_folder(
                        title="branches", count=len(v), node_color=node_color
                    )
                    link(entry, folder, "branches", color=node_color)

                    shown_branches = v[:MAX_EDGES_PER_GROUP]
                    for br in shown_branches:
                        hub = emit_branch_hub(
                            text=_match_branch_label(br), node_color=node_color
                        )
                        link(folder, hub, "", color=node_color, show_label=False)

                        prev = hub

                        tests: list[tuple[str, ASTNode]] = []
                        body_node: Optional[ASTNode] = None
                        for lbl, child in _iter_match_branch_children("branch", br):
                            if _skip_node(child):
                                continue
                            if lbl.endswith(".body"):
                                body_node = child
                                continue
                            tests.append((lbl, child))

                        for lbl, child in tests:
                            c_entry, _ = walk(child, node_color)
                            if c_entry is None:
                                continue
                            short = lbl.removeprefix("branch.")
                            short = short.replace("values[", "v").replace("]", "")
                            short = short.replace("condition", "cond")
                            short = short.replace("pat(", "").replace(")", "")
                            short = short.replace("predicate", "pred")
                            link(prev, c_entry, short, color=node_color, weight=3)
                            prev = c_entry

                        if body_node is not None:
                            b_entry, _ = walk(body_node, node_color)
                            if b_entry is not None:
                                link(prev, b_entry, "body", color=node_color, weight=3)
                                prev = b_entry

                    hidden = len(v) - len(shown_branches)
                    if hidden > 0:
                        more = emit_more(hidden_count=hidden, node_color=node_color)
                        link(folder, more, "more", color=node_color)
                    continue

                # generic list grouping
                if f.name in GROUP_LIST_FIELDS and isinstance(v, (list, tuple)):
                    children = list(_iter_ast_children(f.name, v))
                    if children:
                        folder = emit_folder(
                            title=f.name, count=len(children), node_color=node_color
                        )
                        link(entry, folder, f.name, color=node_color)

                        shown = children[:MAX_EDGES_PER_GROUP]
                        for lbl, child in shown:
                            if _skip_node(child):
                                continue
                            c_entry, c_exit = walk(child, node_color)
                            if c_entry is None:
                                continue
                            short_lbl = lbl.removeprefix(f"{f.name}").lstrip() or "item"
                            link(
                                folder,
                                c_entry,
                                short_lbl if LABEL_NON_FLOW_EDGES else "",
                                color=node_color,
                                show_label=LABEL_NON_FLOW_EDGES,
                            )
                            if isinstance(child, GroupNode) and c_exit is not None:
                                exit_ = c_exit

                        hidden = len(children) - len(shown)
                        if hidden > 0:
                            more = emit_more(hidden_count=hidden, node_color=node_color)
                            link(folder, more, "more", color=node_color)
                        continue

                # generic edge emission
                for lbl, child in _iter_ast_children(f.name, v):
                    if _skip_node(child):
                        continue
                    c_entry, c_exit = walk(child, node_color)
                    if c_entry is None:
                        continue

                    # For asserts, always label if not GroupNode (single node condition / else)
                    if (
                        type(node).__name__ in {"AssertNode", "AssertElseNode"}
                        and f.name == "condition"
                    ):
                        link(
                            entry,
                            c_entry,
                            "cond",
                            color=node_color,
                            show_label=True,
                            weight=3,
                        )
                    elif (
                        type(node).__name__ == "AssertElseNode"
                        and f.name == "else_branch"
                    ):
                        link(
                            entry,
                            c_entry,
                            "else",
                            color=node_color,
                            show_label=True,
                            style="dashed",
                            weight=2,
                        )
                    else:
                        link(
                            entry,
                            c_entry,
                            lbl if LABEL_NON_FLOW_EDGES else "",
                            color=node_color,
                            show_label=LABEL_NON_FLOW_EDGES,
                        )

                    if isinstance(child, GroupNode) and c_exit is not None:
                        exit_ = c_exit

        if _has_exit(node):
            assert structure_color is not None
            exit_marker = emit_exit_marker(entry, node, color=structure_color)

            if exit_ != entry:
                link(exit_, exit_marker, "next", color=structure_color, weight=5)
            elif _needs_forced_exit(node):
                link(entry, exit_marker, "next", color=structure_color, weight=5)

            exit_ = exit_marker

        return (entry, exit_)

    top_entry, _ = walk(root, inherited_color=None)

    dot_lines = [
        "digraph AST {",
        f"  rankdir={rankdir};",
        f'  graph [bgcolor="{BG}", fontname="Consolas", nodesep=0.35, ranksep=0.6];',
        f'  node [fontname="Consolas", fontcolor="{FG}"];',
        f'  edge [fontname="Consolas", fontcolor="{MUTED}", color="{MUTED}"];',
    ]

    if top_entry is not None:
        link("root", top_entry, "program", color=NEUTRAL_BORDER)

    def dedupe(seq: list[str]) -> list[str]:
        seen = set()
        out = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    out_nodes[:] = dedupe(out_nodes)
    out_edges[:] = dedupe(out_edges)

    dot_lines.extend("  " + s for s in out_nodes)
    dot_lines.extend("  " + s for s in out_edges)
    dot_lines.append("}")

    return "\n".join(dot_lines)


def write_dot(dot: str, path: str | Path) -> Path:
    path = Path(path)
    path.write_text(dot, encoding="utf-8")
    return path


def render_with_graphviz(
    dot_path, out_path, fmt: str = "svg", dot_exe: str | None = None
):
    dot_path = Path(dot_path)
    out_path = Path(out_path)

    exe = dot_exe or shutil.which("dot")
    if not exe:
        raise RuntimeError(
            "Graphviz dot.exe not found. Provide dot_exe=... or add it to PATH."
        )

    subprocess.run([exe, f"-T{fmt}", str(dot_path), "-o", str(out_path)], check=True)
    return out_path
