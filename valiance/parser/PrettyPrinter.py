from __future__ import annotations

from dataclasses import is_dataclass, fields
from enum import Enum
from typing import Any
import reprlib


class ParserPrettyPrinter:
    """
    Tree-style pretty-printer intended for AST/debug dumps.

    Goals:
    - No dependency on specific AST node types (no isinstance against AST classes).
    - Include all relevant info (every field of dataclasses, container contents).
    - Readable output for nested structures (tree indentation).
    - Optional per-node override: __pp__(pp) -> str
    """

    def __init__(
        self,
        *,
        indent: int = 2,
        max_depth: int = 80,
        max_seq_items: int | None = None,
        show_private_attrs: bool = False,
    ):
        self.indent = indent
        self.max_depth = max_depth
        self.max_seq_items = max_seq_items
        self.show_private_attrs = show_private_attrs

        self._repr = reprlib.Repr()
        self._repr.maxstring = 300
        self._repr.maxother = 300

    def pformat(self, node: Any) -> str:
        visited: set[int] = set()
        return self._fmt(node, depth=0, visited=visited, prefix="")

    # ---------- formatting core ----------

    def _fmt(self, node: Any, *, depth: int, visited: set[int], prefix: str) -> str:
        if depth > self.max_depth:
            return prefix + "… (max depth)"

        # primitives
        if node is None or isinstance(node, (bool, int, float)):
            return prefix + repr(node)

        if isinstance(node, str):
            return prefix + self._fmt_str(node)

        # enums (TokenType, TagCategory, etc.)
        if isinstance(node, Enum):
            return prefix + f"{type(node).__name__}.{node.name}"

        # per-node override hook
        pp = getattr(node, "__pp__", None)
        if callable(pp):
            # must return a string; you can still call pp.pformat(...) inside __pp__
            return prefix + str(pp(self))

        # cycle safety: apply to "compound" nodes
        oid = id(node)
        if oid in visited:
            return prefix + f"<cycle {type(node).__name__}>"
        compound = self._is_compound(node)
        if compound:
            visited.add(oid)
        try:
            # dataclass: main path for your AST + VTypes
            if is_dataclass(node):
                return self._fmt_dataclass(
                    node, depth=depth, visited=visited, prefix=prefix
                )

            # mappings
            if isinstance(node, dict):
                return self._fmt_dict(node, depth=depth, visited=visited, prefix=prefix)

            # sequences
            if isinstance(node, (list, tuple, set, frozenset)):
                return self._fmt_seq(node, depth=depth, visited=visited, prefix=prefix)

            # plain objects
            if hasattr(node, "__dict__"):
                return self._fmt_object(
                    node, depth=depth, visited=visited, prefix=prefix
                )

            # fallback
            return prefix + self._repr.repr(node)
        finally:
            if compound:
                visited.remove(oid)

    def _is_compound(self, node: Any) -> bool:
        return (
            is_dataclass(node)
            or isinstance(node, (dict, list, tuple, set, frozenset))
            or hasattr(node, "__dict__")
        )

    # ---------- node-type formatters (generic) ----------

    def _fmt_dataclass(
        self, node: Any, *, depth: int, visited: set[int], prefix: str
    ) -> str:
        cls_name = type(node).__name__
        flds = list(fields(node))
        if not flds:
            return prefix + f"{cls_name}()"

        # Header line: NodeType
        lines = [prefix + cls_name]
        child_prefix = prefix + (" " * self.indent)

        for f in flds:
            val = getattr(node, f.name)
            lines.append(
                self._fmt_field(
                    f.name, val, depth=depth, visited=visited, prefix=child_prefix
                )
            )

        return "\n".join(lines)

    def _fmt_object(
        self, node: Any, *, depth: int, visited: set[int], prefix: str
    ) -> str:
        cls_name = type(node).__name__
        d = vars(node)
        items = []
        for k, v in d.items():
            if not self.show_private_attrs and k.startswith("_"):
                continue
            items.append((k, v))

        if not items:
            return prefix + f"{cls_name}()"

        lines = [prefix + cls_name]
        child_prefix = prefix + (" " * self.indent)
        for k, v in items:
            lines.append(
                self._fmt_field(k, v, depth=depth, visited=visited, prefix=child_prefix)
            )
        return "\n".join(lines)

    def _fmt_field(
        self, name: str, val: Any, *, depth: int, visited: set[int], prefix: str
    ) -> str:
        # Decide single-line vs multiline for readability
        if self._is_inlineable(val):
            return prefix + f"{name}: {self._inline(val)}"

        # Multiline: "name:" on one line, children below
        head = prefix + f"{name}:"
        child_prefix = prefix + (" " * self.indent)
        body = self._fmt(val, depth=depth + 1, visited=visited, prefix=child_prefix)
        return head + "\n" + body

    def _fmt_seq(self, seq: Any, *, depth: int, visited: set[int], prefix: str) -> str:
        # Normalize to list for slicing/len
        items = list(seq)

        if self.max_seq_items is not None:
            truncated = len(items) > self.max_seq_items
            items = items[: self.max_seq_items]
        else:
            truncated = False

        typename = type(seq).__name__

        if not items:
            return prefix + f"{typename} []"

        lines = [
            prefix
            + f"{typename} [{len(list(seq)) if hasattr(seq, '__len__') else len(items)}]"
        ]
        child_prefix = prefix + (" " * self.indent)

        for i, item in enumerate(items):
            if self._is_inlineable(item):
                lines.append(child_prefix + f"- {self._inline(item)}")
            else:
                lines.append(child_prefix + "-")
                lines.append(
                    self._fmt(
                        item,
                        depth=depth + 1,
                        visited=visited,
                        prefix=child_prefix + (" " * self.indent),
                    )
                )

        if truncated:
            lines.append(
                child_prefix + f"- … (truncated, max_seq_items={self.max_seq_items})"
            )

        return "\n".join(lines)

    def _fmt_dict(
        self, d: dict[Any, Any], *, depth: int, visited: set[int], prefix: str
    ) -> str:
        if not d:
            return prefix + "dict {}"

        lines = [prefix + f"dict [{len(d)}]"]
        child_prefix = prefix + (" " * self.indent)

        # Keep stable order if keys are sortable; else keep insertion
        try:
            items = sorted(d.items(), key=lambda kv: repr(kv[0]))
        except Exception:
            items = list(d.items())

        if self.max_seq_items is not None:
            truncated = len(items) > self.max_seq_items
            items = items[: self.max_seq_items]
        else:
            truncated = False

        for k, v in items:
            ks = self._inline(k) if self._is_inlineable(k) else self._repr.repr(k)
            if self._is_inlineable(v):
                lines.append(child_prefix + f"{ks}: {self._inline(v)}")
            else:
                lines.append(child_prefix + f"{ks}:")
                lines.append(
                    self._fmt(
                        v,
                        depth=depth + 1,
                        visited=visited,
                        prefix=child_prefix + (" " * self.indent),
                    )
                )

        if truncated:
            lines.append(
                child_prefix + f"…: (truncated, max_seq_items={self.max_seq_items})"
            )

        return "\n".join(lines)

    # ---------- inline heuristics ----------

    def _is_inlineable(self, val: Any) -> bool:
        if val is None or isinstance(val, (bool, int, float)):
            return True
        if isinstance(val, Enum):
            return True
        if isinstance(val, str):
            return len(val) <= 60 and ("\n" not in val)
        if isinstance(val, (list, tuple)) and len(val) == 0:
            return True
        if isinstance(val, dict) and len(val) == 0:
            return True
        # dataclasses are usually NOT inlineable for readability
        return False

    def _inline(self, val: Any) -> str:
        if isinstance(val, str):
            return self._fmt_str(val)
        if isinstance(val, Enum):
            return f"{type(val).__name__}.{val.name}"
        return self._repr.repr(val)

    def _fmt_str(self, s: str) -> str:
        # Keep strings readable but unambiguous
        # If it's identifier-like, show as bare; otherwise repr
        if s and all(c.isalnum() or c in "_-+*/%<>=!?." for c in s) and " " not in s:
            return s
        return repr(s)


def pretty_print_ast(node: Any) -> str:
    return ParserPrettyPrinter().pformat(node)
