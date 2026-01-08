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


def _html_escape(s: str) -> str:
    return html.escape(s, quote=True)


def _ident_to_str(ident: Any) -> str:
    return ident.name if isinstance(ident, Identifier) else str(ident)


def _pretty_value(val: Any) -> str:
    if val is None:
        return ""
    to_string = getattr(val, "toString", None)
    if callable(to_string):
        try:
            return str(to_string())
        except Exception:
            pass
    if isinstance(val, Identifier):
        return _ident_to_str(val)
    return repr(val)


def _skip_node(node: ASTNode) -> bool:
    return isinstance(node, (AuxiliaryNode, AuxiliaryTokenNode))


def _is_ast(x: Any) -> bool:
    return isinstance(x, ASTNode)


def _iter_ast_children(field_name: str, value: Any) -> Iterable[tuple[str, ASTNode]]:
    if value is None:
        return
    if _is_ast(value):
        yield (field_name, value)
        return
    if isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            if _is_ast(item):
                yield (f"{field_name}[{i}]", item)
            elif isinstance(item, tuple) and len(item) == 2:
                a, b = item
                if isinstance(a, Identifier) and _is_ast(b):
                    yield (f"{field_name}[{i}] {_ident_to_str(a)}=", b)
                elif _is_ast(a) and _is_ast(b):
                    yield (f"{field_name}[{i}].0", a)
                    yield (f"{field_name}[{i}].1", b)


def _has_ast_children(node: ASTNode) -> bool:
    """For deciding whether to render as a container card."""
    if isinstance(node, GroupNode):
        return True
    if not is_dataclass(node):
        return False
    for f in fields(node):
        if f.name == "location":
            continue
        v = getattr(node, f.name, None)
        if _is_ast(v):
            return True
        if isinstance(v, (list, tuple)):
            for item in v:
                if _is_ast(item):
                    return True
                if (
                    isinstance(item, tuple)
                    and len(item) == 2
                    and any(_is_ast(x) for x in item)
                ):
                    return True
    return False


def _has_direct_astnode_field(node: ASTNode) -> bool:
    """
    For deciding whether to add an EXIT marker / treat as a structure boundary:
    True only if the node has a direct ASTNode field value (including GroupNode),
    not merely a list/tuple of AST nodes.
    """
    if not is_dataclass(node):
        return False
    for f in fields(node):
        if f.name == "location":
            continue
        v = getattr(node, f.name, None)
        if isinstance(v, ASTNode):
            return True
    return False


def _param_to_line(p: Parameter) -> str:
    name = _ident_to_str(p.name) if getattr(p, "name", None) is not None else "<anon>"
    type_s = _pretty_value(getattr(p, "type_", None))
    cast = getattr(p, "cast", None)
    default = getattr(p, "default", None)

    s = f"{name}"
    if type_s:
        s += f": {type_s}"
    if cast is not None:
        s += f" as {_pretty_value(cast)}"
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

            # children become edges/sequences, not table content
            if _is_ast(v) or isinstance(v, GroupNode):
                continue
            if isinstance(v, (list, tuple)) and any(_is_ast(x) for x in v):
                continue
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

            if isinstance(v, (list, tuple)):
                items = [_pretty_value(x) for x in v]
                cell = (
                    "<BR ALIGN='LEFT'/>".join(f"• {_html_escape(s)}" for s in items)
                    if items
                    else ""
                )
                rows.append((name.capitalize(), cell))
            else:
                rows.append((name.capitalize(), _html_escape(_pretty_value(v))))

    tr_rows = []
    for k, v in rows:
        tr_rows.append(
            "<TR>"
            f"<TD ALIGN='LEFT' BGCOLOR='#E6E6E6'><B>{_html_escape(k)}</B></TD>"
            f"<TD ALIGN='LEFT' BGCOLOR='#F2F2F2'>{v}</TD>"
            "</TR>"
        )

    return (
        "<"
        "<TABLE BORDER='1' CELLBORDER='1' CELLSPACING='0' CELLPADDING='6'>"
        f"<TR><TD COLSPAN='2' BGCOLOR='#FFFFFF' ALIGN='LEFT'><B>{header}</B></TD></TR>"
        + "".join(tr_rows)
        + "</TABLE>"
        ">"
    )


def _simple_box_label(node: ASTNode) -> str:
    parts = [type(node).__name__]
    if is_dataclass(node):
        for f in fields(node):
            if f.name in ("location",):
                continue
            v = getattr(node, f.name, None)
            if v is None:
                continue
            if _is_ast(v) or isinstance(v, GroupNode):
                continue
            if isinstance(v, Identifier):
                parts.append(f"{f.name}={_ident_to_str(v)}")
            elif isinstance(v, (str, int, float, bool)):
                parts.append(f"{f.name}={v}")
    return "\\n".join(_html_escape(p) for p in parts)


def _exit_display_name(node: ASTNode) -> str:
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
    ]

    neutral = "#444444"

    out_nodes.append(
        f'root [shape=box, style="rounded", color="{neutral}", label="ROOT"];'
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

    def get_or_assign_structure_color(entry_id: str) -> str:
        # exit-worthy structures ALWAYS get their own fresh color
        if entry_id not in entry_color:
            entry_color[entry_id] = gen_new_colour()
        return entry_color[entry_id]

    def emit(node: ASTNode, *, node_color: str, penwidth: int) -> str:
        n = nid(node)

        if _has_ast_children(node) and not isinstance(node, GroupNode):
            out_nodes.append(
                f'{n} [shape=plain, color="{node_color}", penwidth={penwidth}, label={_container_table_label(node)}];'
            )
        else:
            out_nodes.append(
                f'{n} [shape=box, color="{node_color}", penwidth={penwidth}, label="{_simple_box_label(node)}"];'
            )
        return n

    def link(a: str, b: str, label: str, *, color: Optional[str] = None) -> None:
        if color:
            out_edges.append(
                f'{a} -> {b} [label="{_html_escape(label)}", color="{color}", fontcolor="{color}"];'
            )
        else:
            out_edges.append(f'{a} -> {b} [label="{_html_escape(label)}"];')

    def link_dotted(a: str, b: str, *, color: str) -> None:
        out_edges.append(
            f'{a} -> {b} [style=dotted, color="{color}", constraint=false, arrowhead=none];'
        )

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

        # Structure boundary?
        structure_color: Optional[str] = None
        if _has_direct_astnode_field(node):
            structure_color = get_or_assign_structure_color(nid(node))

        # IMPORTANT: now every node gets a border color:
        # - if this node starts a structure, use its structure color
        # - else inherit parent structure color if present
        # - else neutral
        node_color = structure_color or inherited_color or neutral
        penwidth = 2 if structure_color else 1

        entry = emit(node, node_color=node_color, penwidth=penwidth)
        exit_ = entry

        # Parameter defaults inherit nearest structure color
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
                for lbl, child in _iter_ast_children(f.name, v):
                    if _skip_node(child):
                        continue
                    c_entry, c_exit = walk(child, node_color)
                    if c_entry is None:
                        continue
                    link(entry, c_entry, lbl, color=node_color)
                    if isinstance(child, GroupNode) and c_exit is not None:
                        exit_ = c_exit

        if _has_direct_astnode_field(node) and exit_ is not None and exit_ != entry:
            assert structure_color is not None
            exit_marker = emit_exit_marker(entry, node, color=structure_color)
            link(
                exit_,
                exit_marker,
                f"exit {_exit_display_name(node)}",
                color=structure_color,
            )
            exit_ = exit_marker

        return (entry, exit_)

    top_entry, _ = walk(root, inherited_color=None)
    if top_entry is not None:
        link("root", top_entry, "program", color=neutral)

    def dedupe(seq: list[str]) -> list[str]:
        seen = set()
        out = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    out_nodes = dedupe(out_nodes)
    out_edges = dedupe(out_edges)

    header = [
        "digraph AST {",
        f"  rankdir={rankdir};",
        '  graph [fontname="Consolas"];',
        '  node [fontname="Consolas"];',
        '  edge [fontname="Consolas"];',
    ]
    footer = ["}"]

    body = ["  " + s for s in (out_nodes + out_edges)]
    return "\n".join(header + body + footer)


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
