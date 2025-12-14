# valiance/parser/PrettyPrinter.py
from __future__ import annotations

from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
from typing import Any
import reprlib


class CompactPrettyPrinter:
    """
    Compact pretty printer for parser output (AST, VTypes, etc.) that does not
    depend on enumerating AST node classes.

    Abbreviation rules (generic):
    - dataclasses printed as TypeName(k=v, ...)
    - omit fields that are equal to their dataclass default/default_factory
    - inline short sequences; truncate long ones as [... xN]
    - limit recursion depth; show TypeName(…) when too deep
    - cycle-safe
    """

    def __init__(
        self,
        *,
        width: int = 100,
        max_depth: int = 12,
        max_seq_items: int = 6,
        inline_seq_items: int = 3,
        indent: int = 2,
        drop_redundant_length_fields: bool = True,
    ):
        self.width = width
        self.max_depth = max_depth
        self.max_seq_items = max_seq_items
        self.inline_seq_items = inline_seq_items
        self.indent = indent
        self.drop_redundant_length_fields = drop_redundant_length_fields

        self._repr = reprlib.Repr()
        self._repr.maxstring = 200
        self._repr.maxother = 200

    def pformat(self, node: Any) -> str:
        visited: set[int] = set()
        return self._fmt(node, depth=0, visited=visited, cur_indent=0)

    def _fmt(self, node: Any, *, depth: int, visited: set[int], cur_indent: int) -> str:
        if depth > self.max_depth:
            return "…"

        # primitives
        if node is None or isinstance(node, (bool, int, float)):
            return repr(node)

        if isinstance(node, str):
            # keep identifiers unquoted if they look like identifiers/operators
            if (
                node
                and all(c.isalnum() or c in "_-+*/%<>=!?." for c in node)
                and " " not in node
            ):
                return node
            return repr(node)

        if isinstance(node, Enum):
            return f"{type(node).__name__}.{node.name}"

        # optional customization hook on nodes
        pp = getattr(node, "__pp__", None)
        if callable(pp):
            return str(pp(self))

        # cycle safety for compound nodes
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
                return self._fmt_dataclass(node, depth, visited, cur_indent)
            if isinstance(node, dict):
                return self._fmt_dict(node, depth, visited, cur_indent)
            if isinstance(node, (list, tuple, set, frozenset)):
                return self._fmt_seq(node, depth, visited, cur_indent)
            if hasattr(node, "__dict__"):
                return self._fmt_object(node, depth, visited, cur_indent)
            return self._repr.repr(node)
        finally:
            if compound:
                visited.remove(oid)

    def _fmt_seq(self, seq: Any, depth: int, visited: set[int], cur_indent: int) -> str:
        items = list(seq)
        n = len(items)

        # inline a few items
        if n == 0:
            return "[]"
        if n <= self.inline_seq_items and all(not is_dataclass(x) for x in items):
            inner = ", ".join(
                self._fmt(x, depth=depth + 1, visited=visited, cur_indent=cur_indent)
                for x in items
            )
            if isinstance(seq, tuple):
                if n == 1:
                    return f"({inner},)"
                return f"({inner})"
            return f"[{inner}]"

        # truncate for readability
        shown = items[: self.max_seq_items]
        inner = ", ".join(
            self._fmt(x, depth=depth + 1, visited=visited, cur_indent=cur_indent)
            for x in shown
        )
        suffix = f", … x{n - self.max_seq_items}" if n > self.max_seq_items else ""
        if isinstance(seq, tuple):
            return f"({inner}{suffix})"
        return f"[{inner}{suffix}]"

    def _fmt_dict(
        self, d: dict[Any, Any], depth: int, visited: set[int], cur_indent: int
    ) -> str:
        if not d:
            return "{}"
        items = list(d.items())
        shown = items[: self.max_seq_items]
        parts = []
        for k, v in shown:
            ks = self._fmt(k, depth=depth + 1, visited=visited, cur_indent=cur_indent)
            vs = self._fmt(v, depth=depth + 1, visited=visited, cur_indent=cur_indent)
            parts.append(f"{ks}: {vs}")
        suffix = (
            f", … x{len(items) - self.max_seq_items}"
            if len(items) > self.max_seq_items
            else ""
        )
        return "{ " + ", ".join(parts) + suffix + " }"

    def _fmt_dataclass(
        self, node: Any, depth: int, visited: set[int], cur_indent: int
    ) -> str:
        cls = type(node)
        name = cls.__name__

        if depth >= self.max_depth:
            return f"{name}(…)"

        # build field list, omitting default-valued fields
        parts: list[str] = []
        flds = list(fields(node))

        # optional generic redundancy drop: if there's a `length` field that matches len(elements/items/options/etc.)
        redundant_length = set()
        if self.drop_redundant_length_fields:
            value_by_name = {f.name: getattr(node, f.name) for f in flds}
            if "length" in value_by_name:
                length_val = value_by_name["length"]
                for candidate in (
                    "elements",
                    "items",
                    "options",
                    "variants",
                    "branches",
                    "entries",
                    "levels",
                ):
                    if candidate in value_by_name and hasattr(
                        value_by_name[candidate], "__len__"
                    ):
                        try:
                            if length_val == len(value_by_name[candidate]):
                                redundant_length.add("length")
                        except Exception:
                            pass

        for f in flds:
            if f.name in redundant_length:
                continue

            val = getattr(node, f.name)

            # omit if equals default value
            if f.default is not MISSING and val == f.default:
                continue
            if f.default_factory is not MISSING:  # type: ignore
                try:
                    if val == f.default_factory():  # type: ignore
                        continue
                except Exception:
                    pass

            vs = self._fmt(val, depth=depth + 1, visited=visited, cur_indent=cur_indent)
            parts.append(f"{f.name}={vs}")

        s = f"{name}(" + ", ".join(parts) + ")"
        if len(s) <= self.width and "\n" not in s:
            return s

        # multiline fallback if it still gets too long
        pad = " " * (cur_indent + self.indent)
        pad0 = " " * cur_indent
        body = (",\n").join(pad + p for p in parts)
        return f"{name}(\n{body}\n{pad0})"

    def _fmt_object(
        self, node: Any, depth: int, visited: set[int], cur_indent: int
    ) -> str:
        name = type(node).__name__
        d = {k: v for k, v in vars(node).items() if not k.startswith("_")}
        if not d:
            return f"{name}()"
        parts = [
            f"{k}={self._fmt(v, depth=depth + 1, visited=visited, cur_indent=cur_indent)}"
            for k, v in d.items()
        ]
        s = f"{name}(" + ", ".join(parts) + ")"
        if len(s) <= self.width and "\n" not in s:
            return s
        pad = " " * (cur_indent + self.indent)
        pad0 = " " * cur_indent
        body = (",\n").join(pad + p for p in parts)
        return f"{name}(\n{body}\n{pad0})"


def pretty_print_ast(node: Any) -> str:
    return CompactPrettyPrinter().pformat(node)
