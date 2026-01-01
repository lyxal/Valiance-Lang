# valiance/parser/PrettyPrinter.py
from __future__ import annotations

from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
from typing import Any
import reprlib


class ReadableCompactPP:
    def __init__(
        self,
        *,
        width: int = 100,
        indent: int = 2,
        max_depth: int = 20,
        max_seq_items: int = 20,
        inline_seq_items: int = 4,
        show_locations: bool = True,
        location_field: str = "location",
        drop_default_fields: bool = True,
    ):
        self.width = width
        self.indent = indent
        self.max_depth = max_depth
        self.max_seq_items = max_seq_items
        self.inline_seq_items = inline_seq_items
        self.show_locations = show_locations
        self.location_field = location_field
        self.drop_default_fields = drop_default_fields

        self._repr = reprlib.Repr()
        self._repr.maxstring = 200
        self._repr.maxother = 200

    def pformat(self, node: Any) -> str:
        visited: set[int] = set()
        return self._fmt(node, depth=0, visited=visited, cur_indent=0)

    # ---------------- core ----------------

    def _fmt(self, node: Any, *, depth: int, visited: set[int], cur_indent: int) -> str:
        if depth > self.max_depth:
            return "…"

        if node is None or isinstance(node, (bool, int, float)):
            return repr(node)

        if isinstance(node, str):
            if (
                node
                and all(c.isalnum() or c in "_-+*/%<>=!?." for c in node)
                and " " not in node
            ):
                return node
            return repr(node)

        if isinstance(node, Enum):
            return f"{type(node).__name__}.{node.name}"

        hook = getattr(node, "__pp__", None)
        if callable(hook):
            return str(hook(self))

        compound = (
            is_dataclass(node)
            or isinstance(node, (dict, list, tuple, set, frozenset))
            or hasattr(node, "__dict__")
        )
        oid = id(node)
        if compound:
            if oid in visited:
                return f"<cycle {type(node).__name__}>"
            visited.add(oid)
        try:
            if is_dataclass(node):
                return self._fmt_dataclass(
                    node, depth=depth, visited=visited, cur_indent=cur_indent
                )
            if isinstance(node, dict):
                return self._fmt_dict(
                    node, depth=depth, visited=visited, cur_indent=cur_indent
                )
            if isinstance(node, (list, tuple, set, frozenset)):
                return self._fmt_seq(
                    node, depth=depth, visited=visited, cur_indent=cur_indent
                )
            if hasattr(node, "__dict__"):
                return self._fmt_object(
                    node, depth=depth, visited=visited, cur_indent=cur_indent
                )
            return self._repr.repr(node)
        finally:
            if compound:
                visited.remove(oid)

    # ---------------- heuristics ----------------

    def _maybe_loc_suffix(self, node: Any) -> str:
        """
        If node has a dataclass field named `location` with (line, column), show as "@L:C".
        This is AST-agnostic: only relies on field names.
        """
        if not self.show_locations or not is_dataclass(node):
            return ""
        try:
            loc = getattr(node, self.location_field)
        except Exception:
            return ""
        if loc is None:
            return ""
        # accept either dataclass/obj with .line/.column or dict-like
        line = getattr(loc, "line", None)
        col = getattr(loc, "column", None)
        if line is None or col is None:
            return ""
        return f" @{line}:{col}"

    def _drop_field_as_default(self, f, val: Any) -> bool:
        if not self.drop_default_fields:
            return False
        if f.default is not MISSING and val == f.default:
            return True
        if f.default_factory is not MISSING:  # type: ignore
            try:
                if val == f.default_factory():  # type: ignore
                    return True
            except Exception:
                pass
        return False

    def _is_pair_list(self, val: Any) -> bool:
        # list of 2-tuples (common for dict entries/branches/etc.)
        if not isinstance(val, list) or not val:
            return False
        for x in val:
            if not (isinstance(x, tuple) and len(x) == 2):
                return False
        return True

    # ---------------- formatters ----------------

    def _fmt_dataclass(
        self, node: Any, *, depth: int, visited: set[int], cur_indent: int
    ) -> str:
        name = type(node).__name__
        locsuf = self._maybe_loc_suffix(node)

        flds = list(fields(node))
        if not flds:
            return f"{name}{locsuf}()"

        # collect fields, but optionally omit defaults and optionally omit the verbose location object
        parts: list[tuple[str, Any]] = []
        for f in flds:
            val = getattr(node, f.name)

            # don't print location as a full subobject if we're showing @line:col already
            if self.show_locations and f.name == self.location_field:
                continue

            if self._drop_field_as_default(f, val):
                continue

            parts.append((f.name, val))

        # If it fits on one line, do it
        inline_parts = [
            f"{k}={self._fmt(v, depth=depth+1, visited=visited, cur_indent=cur_indent)}"
            for k, v in parts
        ]
        one_line = f"{name}{locsuf}(" + ", ".join(inline_parts) + ")"
        if len(one_line) <= self.width and "\n" not in one_line:
            return one_line

        # Multiline: each field on its own line; special-case pair-lists for readability
        pad0 = " " * cur_indent
        pad = " " * (cur_indent + self.indent)
        lines = [f"{name}{locsuf}("]
        for k, v in parts:
            if self._is_pair_list(v):
                lines.append(f"{pad}{k}=[")
                lines.extend(
                    self._fmt_pair_list(
                        v,
                        depth=depth + 1,
                        visited=visited,
                        cur_indent=cur_indent + 2 * self.indent,
                    )
                )
                lines.append(f"{pad}]")
            else:
                vv = self._fmt(
                    v,
                    depth=depth + 1,
                    visited=visited,
                    cur_indent=cur_indent + self.indent,
                )
                if "\n" in vv:
                    lines.append(f"{pad}{k}=")
                    # indent vv by one more level
                    vv_ind = self._indent_block(vv, cur_indent + 2 * self.indent)
                    lines.append(vv_ind)
                else:
                    lines.append(f"{pad}{k}={vv}")
        lines.append(f"{pad0})")
        return "\n".join(lines)

    def _fmt_pair_list(
        self,
        items: list[tuple[Any, Any]],
        *,
        depth: int,
        visited: set[int],
        cur_indent: int,
    ) -> list[str]:
        # render (k, v) as "k -> v"
        pad = " " * cur_indent
        out: list[str] = []
        shown = items[: self.max_seq_items]
        for k, v in shown:
            ks = self._fmt(k, depth=depth + 1, visited=visited, cur_indent=cur_indent)
            vs = self._fmt(v, depth=depth + 1, visited=visited, cur_indent=cur_indent)
            out.append(f"{pad}{ks} -> {vs},")
        if len(items) > self.max_seq_items:
            out.append(f"{pad}… x{len(items) - self.max_seq_items}")
        return out

    def _fmt_seq(
        self, seq: Any, *, depth: int, visited: set[int], cur_indent: int
    ) -> str:
        items = list(seq)
        n = len(items)
        shown = items[: self.max_seq_items]

        if n == 0:
            return "[]"

        # try inline if short and simple
        if n <= self.inline_seq_items and all(self._is_inlineable(x) for x in items):
            inner = ", ".join(
                self._fmt(x, depth=depth + 1, visited=visited, cur_indent=cur_indent)
                for x in items
            )
            if isinstance(seq, tuple) and n == 1:
                return f"({inner},)"
            if isinstance(seq, tuple):
                return f"({inner})"
            return f"[{inner}]"

        # multiline list
        pad0 = " " * cur_indent
        pad = " " * (cur_indent + self.indent)
        lines = ["["]
        for x in shown:
            s = self._fmt(
                x, depth=depth + 1, visited=visited, cur_indent=cur_indent + self.indent
            )
            if "\n" in s:
                lines.append(f"{pad}-")
                lines.append(self._indent_block(s, cur_indent + self.indent))
            else:
                lines.append(f"{pad}- {s}")
        if n > self.max_seq_items:
            lines.append(f"{pad}- … x{n - self.max_seq_items}")
        lines.append(f"{pad0}]")
        return "\n".join(lines)

    def _fmt_dict(
        self, d: dict[Any, Any], *, depth: int, visited: set[int], cur_indent: int
    ) -> str:
        if not d:
            return "{}"
        items = list(d.items())[: self.max_seq_items]
        inner = ", ".join(
            f"{self._fmt(k, depth=depth+1, visited=visited, cur_indent=cur_indent)}: {self._fmt(v, depth=depth+1, visited=visited, cur_indent=cur_indent)}"
            for k, v in items
        )
        suffix = (
            f", … x{len(d) - self.max_seq_items}" if len(d) > self.max_seq_items else ""
        )
        s = "{ " + inner + suffix + " }"
        return s if len(s) <= self.width else "{…}"

    def _fmt_object(
        self, node: Any, *, depth: int, visited: set[int], cur_indent: int
    ) -> str:
        name = type(node).__name__
        d = {k: v for k, v in vars(node).items() if not k.startswith("_")}
        if not d:
            return f"{name}()"
        inner = ", ".join(
            f"{k}={self._fmt(v, depth=depth+1, visited=visited, cur_indent=cur_indent)}"
            for k, v in d.items()
        )
        s = f"{name}({inner})"
        return s if len(s) <= self.width else f"{name}(…)"

    def _is_inlineable(self, x: Any) -> bool:
        return x is None or isinstance(x, (bool, int, float, str, Enum))

    def _indent_block(self, s: str, indent: int) -> str:
        pad = " " * indent
        return "\n".join(pad + line if line else line for line in s.splitlines())


def pretty_print_ast(node: Any) -> str:
    return ReadableCompactPP(width=400).pformat(node)
