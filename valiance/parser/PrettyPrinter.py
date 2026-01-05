from __future__ import annotations

from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
from typing import Any
import reprlib


class ReadableCompactPP:
    """
    Compact pretty-printer for ASTs with controlled indentation.

    Design goals:
    - Keep indentation shallow (one level per nesting).
    - Prefer inline formatting up to `width`.
    - When multiline is needed, avoid compounding indentation:
        field=
          <multiline value>
      not:
        field=
            <multiline value>
    - Lists: inline if short, else multiline with one-indent-per-level.
    - Dataclasses: show "@line:col" and omit printing the full location object.
    """

    def __init__(
        self,
        *,
        width: int = 200,
        indent: int = 2,
        max_depth: int = 30,
        max_seq_items: int = 60,
        inline_seq_items: int = 6,
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

        # Avoid importing Identifier (cycle-safe). Use its repr.
        if type(node).__name__ == "Identifier":
            return repr(node)

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
        if not self.show_locations or not is_dataclass(node):
            return ""
        try:
            loc = getattr(node, self.location_field)
        except Exception:
            return ""
        if loc is None:
            return ""
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
        # list of 2-tuples (common for args/branches/entries)
        return (
            isinstance(val, list)
            and bool(val)
            and all(isinstance(x, tuple) and len(x) == 2 for x in val)
        )

    # ---------------- helpers ----------------

    def _indent_block(self, s: str, indent: int) -> str:
        pad = " " * indent
        return "\n".join(pad + line if line else line for line in s.splitlines())

    def _try_inline(self, s: str) -> bool:
        return "\n" not in s and len(s) <= self.width

    # ---------------- formatters ----------------

    def _fmt_dataclass(
        self, node: Any, *, depth: int, visited: set[int], cur_indent: int
    ) -> str:
        name = type(node).__name__
        locsuf = self._maybe_loc_suffix(node)

        flds = list(fields(node))
        if not flds:
            return f"{name}{locsuf}()"

        parts: list[tuple[str, Any]] = []
        for f in flds:
            val = getattr(node, f.name)

            if self.show_locations and f.name == self.location_field:
                continue
            if self._drop_field_as_default(f, val):
                continue
            parts.append((f.name, val))

        # Inline attempt
        inline_parts = [
            f"{k}={self._fmt(v, depth=depth+1, visited=visited, cur_indent=cur_indent)}"
            for k, v in parts
        ]
        one_line = f"{name}{locsuf}(" + ", ".join(inline_parts) + ")"
        if self._try_inline(one_line):
            return one_line

        # Multiline
        pad0 = " " * cur_indent
        pad = " " * (cur_indent + self.indent)
        lines: list[str] = [f"{name}{locsuf}("]

        for k, v in parts:
            if self._is_pair_list(v):
                # Keep pair-lists very compact:
                # args=[
                #   a -> b,
                # ]
                lines.append(f"{pad}{k}=[")
                lines.extend(
                    self._fmt_pair_list(
                        v,
                        depth=depth + 1,
                        visited=visited,
                        cur_indent=cur_indent + 2 * self.indent,
                    )
                )
                lines.append(f"{pad}],")
                continue

            vv = self._fmt(
                v,
                depth=depth + 1,
                visited=visited,
                cur_indent=cur_indent + self.indent,
            )

            if "\n" not in vv:
                lines.append(f"{pad}{k}={vv},")
            else:
                # Shallow multiline: field= then value indented by ONE level
                lines.append(f"{pad}{k}=")
                lines.append(self._indent_block(vv, cur_indent + 2 * self.indent))
                lines[-1] = lines[-1] + ","

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
        pad = " " * cur_indent
        out: list[str] = []
        shown = items[: self.max_seq_items]
        for k, v in shown:
            ks = self._fmt(k, depth=depth + 1, visited=visited, cur_indent=cur_indent)
            vs = self._fmt(v, depth=depth + 1, visited=visited, cur_indent=cur_indent)

            if "\n" in ks or "\n" in vs:
                # Rare, but keep readable without exploding indentation.
                out.append(f"{pad}(")
                out.append(
                    self._indent_block(f"{ks} -> {vs}", cur_indent + self.indent)
                )
                out.append(f"{pad}),")
            else:
                out.append(f"{pad}{ks} -> {vs},")
        if len(items) > self.max_seq_items:
            out.append(f"{pad}… x{len(items) - self.max_seq_items}")
        return out

    def _fmt_seq(
        self, seq: Any, *, depth: int, visited: set[int], cur_indent: int
    ) -> str:
        items = list(seq)
        n = len(items)
        if n == 0:
            return "[]"

        # Inline attempt for short lists/tuples
        if n <= self.inline_seq_items:
            rendered = [
                self._fmt(x, depth=depth + 1, visited=visited, cur_indent=cur_indent)
                for x in items
            ]
            if all("\n" not in s for s in rendered):
                inner = ", ".join(rendered)
                if isinstance(seq, tuple) and n == 1:
                    s = f"({inner},)"
                elif isinstance(seq, tuple):
                    s = f"({inner})"
                else:
                    s = f"[{inner}]"
                if self._try_inline(s):
                    return s

        # Multiline list
        pad0 = " " * cur_indent
        pad = " " * (cur_indent + self.indent)
        lines = ["["]
        shown = items[: self.max_seq_items]
        for x in shown:
            s = self._fmt(
                x, depth=depth + 1, visited=visited, cur_indent=cur_indent + self.indent
            )
            if "\n" in s:
                # indent the block under the list bullet by one level
                lines.append(f"{pad}{s.replace(chr(10), chr(10) + pad)},")
            else:
                lines.append(f"{pad}{s},")
        if n > self.max_seq_items:
            lines.append(f"{pad}… x{n - self.max_seq_items}")
        lines.append(f"{pad0}]")
        return "\n".join(lines)

    def _fmt_dict(
        self, d: dict[Any, Any], *, depth: int, visited: set[int], cur_indent: int
    ) -> str:
        if not d:
            return "{}"
        items = list(d.items())[: self.max_seq_items]
        rendered = [
            (
                self._fmt(k, depth=depth + 1, visited=visited, cur_indent=cur_indent),
                self._fmt(v, depth=depth + 1, visited=visited, cur_indent=cur_indent),
            )
            for k, v in items
        ]

        if all("\n" not in ks and "\n" not in vs for ks, vs in rendered):
            inner = ", ".join(f"{ks}: {vs}" for ks, vs in rendered)
            suffix = (
                f", … x{len(d) - self.max_seq_items}"
                if len(d) > self.max_seq_items
                else ""
            )
            s = "{ " + inner + suffix + " }"
            if self._try_inline(s):
                return s

        pad0 = " " * cur_indent
        pad = " " * (cur_indent + self.indent)
        lines = ["{"]
        for ks, vs in rendered:
            if "\n" in vs:
                vs = vs.replace("\n", "\n" + pad)
            lines.append(f"{pad}{ks}: {vs},")
        if len(d) > self.max_seq_items:
            lines.append(f"{pad}… x{len(d) - self.max_seq_items}")
        lines.append(f"{pad0}}}")
        return "\n".join(lines)

    def _fmt_object(
        self, node: Any, *, depth: int, visited: set[int], cur_indent: int
    ) -> str:
        name = type(node).__name__
        d = {k: v for k, v in vars(node).items() if not k.startswith("_")}
        if not d:
            return f"{name}()"

        inline_parts = [
            f"{k}={self._fmt(v, depth=depth+1, visited=visited, cur_indent=cur_indent)}"
            for k, v in d.items()
        ]
        one_line = f"{name}(" + ", ".join(inline_parts) + ")"
        if self._try_inline(one_line):
            return one_line

        pad0 = " " * cur_indent
        pad = " " * (cur_indent + self.indent)
        lines = [f"{name}("]
        for k, v in d.items():
            vv = self._fmt(
                v,
                depth=depth + 1,
                visited=visited,
                cur_indent=cur_indent + self.indent,
            )
            if "\n" in vv:
                lines.append(f"{pad}{k}=")
                lines.append(self._indent_block(vv, cur_indent + 2 * self.indent))
                lines[-1] = lines[-1] + ","
            else:
                lines.append(f"{pad}{k}={vv},")
        lines.append(f"{pad0})")
        return "\n".join(lines)


def pretty_print_ast(node: Any) -> str:
    return ReadableCompactPP(width=100).pformat(node)
