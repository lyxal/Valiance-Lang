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
# Show compact inline summaries for these list fields (table only)
INLINE_AST_LIST_FIELD_NAMES = {
    # element-call-ish
    "arguments",
    "args",
    "modifier_args",
    # common collections
    "items",
    "elements",
    "branches",
    "entries",
    "variants",
    # OO collections
    "required_methods",
    "default_methods",
    "variant_objects",
    "fields",
    "members",
    "methods",
    "parent_traits",
    # object ctor bits
    "default_constructor",
}
MAX_INLINE_LIST_ITEMS = 6
MAX_INLINE_STRING = 60

# Cleaner output: group list fields behind a "folder" node, and cap shown items
GROUP_LIST_FIELDS = {
    # element-call-ish (keeps large calls readable)
    "args",
    "modifier_args",
    # OO / decl
    "required_methods",
    "default_methods",
    "variant_objects",
    "fields",
    "members",
    "methods",
    "parent_traits",
    "variants",
    # other potentially-big lists
    "branches",
    "entries",
    "items",
    "elements",
    # object ctor bits
    "default_constructor",
}
MAX_EDGES_PER_GROUP = 12  # number of children shown per grouped list node


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
    if val is None:
        return ""
    to_string = getattr(val, "toString", None)
    if callable(to_string):
        try:
            return _short(str(to_string()))
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


# -------- MatchBranch support --------


def _is_match_branch(obj: Any) -> bool:
    """
    MatchBranch objects are not dataclasses. Identify by duck-typing:
    - has a body: ASTNode
    - class name starts with "Match" and ends with "Branch" (keeps it conservative)
    """
    if obj is None:
        return False
    if is_dataclass(obj):
        return False
    tn = type(obj).__name__
    if not (tn.startswith("Match") and tn.endswith("Branch")):
        return False
    return isinstance(getattr(obj, "body", None), ASTNode)


def _match_branch_label(branch: Any) -> str:
    tn = type(branch).__name__
    if tn == "MatchExactBranch":
        vals = getattr(branch, "values", None)
        if isinstance(vals, list):
            return f"exact[{len(vals)}]"
        return "exact"
    if tn == "MatchIfBranch":
        return "if"
    if tn == "MatchPatternBranch":
        return "pattern"
    if tn == "MatchAsBranch":
        name = getattr(branch, "name", None)
        type_ = getattr(branch, "type_", None)
        parts: list[str] = []
        if isinstance(name, Identifier):
            parts.append(_ident_to_str(name))
        if type_ is not None:
            parts.append(_pretty_scalar(type_))
        inner = ": ".join(parts) if parts else "as"
        return f"as({inner})"
    if tn == "MatchDefaultBranch":
        return "default"
    return tn.removesuffix("Branch").removeprefix("Match").lower() or tn


def _iter_match_branch_children(
    prefix: str, branch: Any
) -> Iterable[tuple[str, ASTNode]]:
    """
    Yield AST children for a branch object.
    """
    tn = type(branch).__name__

    # shared body
    body = getattr(branch, "body", None)
    if isinstance(body, ASTNode):
        yield (f"{prefix}.body", body)

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
        if isinstance(pat, ASTNode):
            yield (f"{prefix}.pattern", pat)

    elif tn == "MatchAsBranch":
        # name/type_ are scalar-ish; only body is AST, already handled above
        pass

    elif tn == "MatchDefaultBranch":
        pass


# -------- core formatting / signature --------


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

    # Special-case match branches (non-dataclass objects)
    if seq and all(_is_match_branch(x) for x in seq):
        items = [
            f"• {_html_escape(_match_branch_label(b))}"
            for b in seq[:MAX_INLINE_LIST_ITEMS]
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

    # MatchBranch objects
    if _is_match_branch(value):
        yield from _iter_match_branch_children(field_name, value)
        return

    if isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            # list of MatchBranch objects
            if _is_match_branch(item):
                yield from _iter_match_branch_children(
                    f"{field_name}[{i}] {_match_branch_label(item)}", item
                )
                continue

            if isinstance(item, ASTNode):
                yield (f"{field_name}[{i}]", item)
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
    return type(node).__name__ in {
        "ObjectDefinitionNode",
        "ObjectTraitImplNode",
        "TraitNode",
        "TraitImplTraitNode",
        "MatchNode",
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

            # DefineNode.element_tags: join on " + "
            if name == "element_tags" and isinstance(v, list):
                rows.append(
                    (
                        name.capitalize(),
                        _html_escape(" + ".join(_pretty_scalar(t) for t in v)),
                    )
                )
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

            # Show small string-label lists (Swap/Dup/Pop)
            if isinstance(v, (list, tuple)):
                if all(isinstance(x, str) for x in v):
                    parts.append(f"{f.name}=[{','.join(v)}]")
                continue

            if isinstance(v, Identifier):
                parts.append(f"{f.name}={_ident_to_str(v)}")
            elif isinstance(v, (str, int, float, bool)):
                parts.append(f"{f.name}={v}")
            else:
                # e.g. VType
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

    # High-contrast, wildly varied palette for clear visual separation
    palette = [
        "#1F77B4",  # vivid blue
        "#E74C3C",  # bright red
        "#2ECC71",  # bright green
        "#F1C40F",  # strong yellow
        "#9B59B6",  # saturated purple
        "#16A085",  # teal
        "#E67E22",  # orange
        "#00BCD4",  # cyan
        "#FF00FF",  # magenta
        "#7FFF00",  # chartreuse
        "#0B3C5D",  # very dark navy
        "#641E16",  # deep maroon
        "#145A32",  # dark forest green
        "#7D6608",  # dark gold
        "#4A235A",  # deep violet
        "#0E6251",  # dark teal
        "#784212",  # dark brown-orange
        "#1B2631",  # near-black blue-gray
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
        label = f"{title} ({count})"
        out_nodes.append(
            f'{fid} [shape=box, style="rounded", penwidth=1, color="{node_color}", '
            f'fontcolor="{FG}", label="{_html_escape(label)}"];'
        )
        return fid

    def emit_more(*, hidden_count: int, node_color: str) -> str:
        mid = new_anon("more")
        out_nodes.append(
            f'{mid} [shape=box, style="rounded,dashed", penwidth=1, color="{node_color}", '
            f'fontcolor="{MUTED}", label="{_html_escape("… (+" + str(hidden_count) + " more)")}"];'
        )
        return mid

    def link(a: str, b: str, label: str, *, color: Optional[str] = None) -> None:
        c = color or MUTED
        out_edges.append(
            f'{a} -> {b} [label="{_html_escape(label)}", color="{c}", fontcolor="{c}"];'
        )

    def link_dotted(a: str, b: str, *, color: str) -> None:
        out_edges.append(f'{a} -> {b} [style=dotted, color="{color}", arrowhead=none];')

    def emit_exit_marker(entry_id: str, node: ASTNode, *, color: str) -> str:
        if entry_id in exit_ids:
            return exit_ids[entry_id]
        eid = f"{entry_id}_exit"
        exit_ids[entry_id] = eid

        who = _exit_display_name(node)
        out_nodes.append(
            f'{eid} [shape=box, style="rounded,dashed", penwidth=2, color="{color}", '
            f'fontcolor="{color}", label="{_html_escape("EXIT " + who)}"];'
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
                    link(prev_exit, c_entry, "next", color=inherited_color)
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
                            link(folder, c_entry, short_lbl, color=node_color)

                        hidden = len(children) - len(shown)
                        if hidden > 0:
                            more = emit_more(hidden_count=hidden, node_color=node_color)
                            link(folder, more, "more", color=node_color)
                        continue

                for lbl, child in _iter_ast_children(f.name, v):
                    if _skip_node(child):
                        continue
                    c_entry, c_exit = walk(child, node_color)
                    if c_entry is None:
                        continue
                    link(entry, c_entry, lbl, color=node_color)
                    if isinstance(child, GroupNode) and c_exit is not None:
                        exit_ = c_exit

        if _has_exit(node):
            assert structure_color is not None
            exit_marker = emit_exit_marker(entry, node, color=structure_color)

            if exit_ != entry:
                link(exit_, exit_marker, "next", color=structure_color)
            elif _needs_forced_exit(node):
                link(entry, exit_marker, "next", color=structure_color)

            exit_ = exit_marker

        return (entry, exit_)

    top_entry, _ = walk(root, inherited_color=None)

    dot_lines = [
        "digraph AST {",
        "  rankdir=TB;",
        f'  graph [bgcolor="{BG}", fontname="Consolas"];',
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
