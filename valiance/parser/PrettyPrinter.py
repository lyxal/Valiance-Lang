"""Pretty-printer utilities for parser AST nodes.

This module provides functions to format AST nodes in tree-like formats
for debugging and visualization purposes.
"""

from typing import Any, Optional, Sequence, Tuple

from valiance.parser.AST import (AliasedImportNode, AssertElseNode, AssertNode,
                                 ASTNode, AtNode, AugmentedVariableSetNode,
                                 BranchNode, ConstantSetNode, DefineNode,
                                 DuplicateNode, ElementNode, ForNode,
                                 FunctionNode, GroupNode, IfNode, ListNode,
                                 LiteralNode, MatchNode, ModuleImportNode,
                                 ObjectNode, SwapNode, TraitNode, TupleNode,
                                 TypeCastNode, TypeNode, VariableGetNode,
                                 VariableSetNode, VariantNode, WhileNode)


def _format_value(value: Any, indent: int = 0) -> str:
    """Format a value for display, handling various types.

    Args:
        value: The value to format
        indent: Current indentation level

    Returns:
        A formatted string representation of the value
    """
    if value is None:
        return "None"
    elif isinstance(value, str):
        return repr(value)
    elif isinstance(value, bool):
        return str(value)
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        if not value:
            return "[]"
        items = ", ".join(_format_value(item, indent) for item in value)
        return f"[{items}]"
    elif isinstance(value, tuple):
        if not value:
            return "()"
        items = ", ".join(_format_value(item, indent) for item in value)
        return f"({items})"
    else:
        return str(value)


def _format_ast_node(
    node: ASTNode,
    indent: int = 0,
    max_depth: Optional[int] = None,
    current_depth: int = 0,
) -> str:
    """Format an AST node recursively with proper indentation.

    Args:
        node: The AST node to format
        indent: Current indentation level (spaces)
        max_depth: Maximum depth to traverse (None for unlimited)
        current_depth: Current depth in the tree

    Returns:
        A formatted string representation of the AST node
    """
    indent_str = " " * indent

    if max_depth is not None and current_depth >= max_depth:
        return f"{indent_str}{node.__class__.__name__} [...]"

    if isinstance(node, GroupNode):
        if not node.elements:
            return f"{indent_str}GroupNode([])"
        lines = [f"{indent_str}GroupNode(["]
        for elem in node.elements:
            lines.append(
                _format_ast_node(elem, indent + 2, max_depth, current_depth + 1)
            )
        lines.append(f"{indent_str}])")
        return "\n".join(lines)

    elif isinstance(node, ElementNode):
        lines = [f"{indent_str}ElementNode("]
        lines.append(f"{indent_str}  name={repr(node.element_name)}")
        if node.generics:
            lines.append(f"{indent_str}  generics={_format_value(node.generics)}")
        if node.args:
            lines.append(f"{indent_str}  args=[")
            for name, arg_node in node.args:
                lines.append(f"{indent_str}    {repr(name)}:")
                lines.append(
                    _format_ast_node(arg_node, indent + 6, max_depth, current_depth + 1)
                )
            lines.append(f"{indent_str}  ]")
        if node.modified:
            lines.append(f"{indent_str}  modified=True")
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, LiteralNode):
        return f"{indent_str}LiteralNode(value={repr(node.value)}, type={node.type_})"

    elif isinstance(node, TupleNode):
        if not node.elements:
            return f"{indent_str}TupleNode([])"
        lines = [f"{indent_str}TupleNode(["]
        for elem in node.elements:
            lines.append(
                _format_ast_node(elem, indent + 2, max_depth, current_depth + 1)
            )
        lines.append(f"{indent_str}])")
        return "\n".join(lines)

    elif isinstance(node, TypeNode):
        return f"{indent_str}TypeNode(type={repr(node.type_)})"

    elif isinstance(node, DefineNode):
        lines = [f"{indent_str}DefineNode("]
        lines.append(f"{indent_str}  name={repr(node.name)}")
        if node.generics:
            lines.append(f"{indent_str}  generics={_format_value(node.generics)}")
        if node.parameters:
            lines.append(f"{indent_str}  parameters=[")
            for name, type_node in node.parameters:
                lines.append(f"{indent_str}    {repr(name)}: {type_node.type_}")
            lines.append(f"{indent_str}  ]")
        if node.output:
            lines.append(f"{indent_str}  output={_format_value(node.output)}")
        lines.append(f"{indent_str}  body:")
        lines.append(
            _format_ast_node(node.body, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, VariantNode):
        lines = [f"{indent_str}VariantNode("]
        lines.append(f"{indent_str}  options=[")
        for obj in node.options:
            lines.append(
                _format_ast_node(obj, indent + 4, max_depth, current_depth + 1)
            )
        lines.append(f"{indent_str}  ]")
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, ObjectNode):
        lines = [f"{indent_str}ObjectNode("]
        lines.append(f"{indent_str}  name={repr(node.name)}")
        if node.generics:
            lines.append(f"{indent_str}  generics={_format_value(node.generics)}")
        if node.implemented_traits:
            lines.append(
                f"{indent_str}  implemented_traits={_format_value(node.implemented_traits)}"
            )
        lines.append(f"{indent_str}  body:")
        lines.append(
            _format_ast_node(node.body, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, TraitNode):
        lines = [f"{indent_str}TraitNode("]
        lines.append(f"{indent_str}  name={repr(node.name)}")
        if node.generics:
            lines.append(f"{indent_str}  generics={_format_value(node.generics)}")
        if node.other_traits:
            lines.append(
                f"{indent_str}  other_traits={_format_value(node.other_traits)}"
            )
        lines.append(f"{indent_str}  body:")
        lines.append(
            _format_ast_node(node.body, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, ListNode):
        if not node.items:
            return f"{indent_str}ListNode([])"
        lines = [f"{indent_str}ListNode(["]
        for item in node.items:
            lines.append(
                _format_ast_node(item, indent + 2, max_depth, current_depth + 1)
            )
        lines.append(f"{indent_str}])")
        return "\n".join(lines)

    elif isinstance(node, FunctionNode):
        lines = [f"{indent_str}FunctionNode("]
        if node.parameters:
            lines.append(f"{indent_str}  parameters=[")
            for name, type_node in node.parameters:
                lines.append(f"{indent_str}    {repr(name)}: {type_node.type_}")
            lines.append(f"{indent_str}  ]")
        if node.output:
            lines.append(f"{indent_str}  output={_format_value(node.output)}")
        lines.append(f"{indent_str}  body:")
        lines.append(
            _format_ast_node(node.body, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, VariableGetNode):
        return f"{indent_str}VariableGetNode(name={repr(node.name)})"

    elif isinstance(node, VariableSetNode):
        lines = [f"{indent_str}VariableSetNode("]
        lines.append(f"{indent_str}  name={repr(node.name)}")
        lines.append(f"{indent_str}  value:")
        lines.append(
            _format_ast_node(node.value, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, AugmentedVariableSetNode):
        lines = [f"{indent_str}AugmentedVariableSetNode("]
        lines.append(f"{indent_str}  name={repr(node.name)}")
        lines.append(f"{indent_str}  function:")
        lines.append(
            _format_ast_node(node.function, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, DuplicateNode):
        return f"{indent_str}DuplicateNode(prestack={node.prestack}, poststack={node.poststack})"

    elif isinstance(node, SwapNode):
        return f"{indent_str}SwapNode(prestack={node.prestack}, poststack={node.poststack})"

    elif isinstance(node, ModuleImportNode):
        return f"{indent_str}ModuleImportNode(module={repr(node.module_name)}, components={node.components})"

    elif isinstance(node, AliasedImportNode):
        return f"{indent_str}AliasedImportNode(original={repr(node.original_name)}, alias={repr(node.alias_name)})"

    elif isinstance(node, ConstantSetNode):
        lines = [f"{indent_str}ConstantSetNode("]
        lines.append(f"{indent_str}  name={repr(node.name)}")
        lines.append(f"{indent_str}  value:")
        lines.append(
            _format_ast_node(node.value, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, TypeCastNode):
        return f"{indent_str}TypeCastNode(target_type={node.target_type.type_})"

    elif isinstance(node, IfNode):
        lines = [f"{indent_str}IfNode("]
        lines.append(f"{indent_str}  condition:")
        lines.append(
            _format_ast_node(node.condition, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str}  then:")
        lines.append(
            _format_ast_node(node.then_branch, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, BranchNode):
        lines = [f"{indent_str}BranchNode("]
        lines.append(f"{indent_str}  condition:")
        lines.append(
            _format_ast_node(node.condition, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str}  then:")
        lines.append(
            _format_ast_node(node.then_branch, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str}  else:")
        lines.append(
            _format_ast_node(node.else_branch, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, MatchNode):
        lines = [f"{indent_str}MatchNode("]
        lines.append(f"{indent_str}  branches=[")
        for condition, body in node.branches:
            lines.append(f"{indent_str}    condition:")
            lines.append(
                _format_ast_node(condition, indent + 6, max_depth, current_depth + 1)
            )
            lines.append(f"{indent_str}    body:")
            lines.append(
                _format_ast_node(body, indent + 6, max_depth, current_depth + 1)
            )
        lines.append(f"{indent_str}  ]")
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, AssertNode):
        lines = [f"{indent_str}AssertNode("]
        lines.append(f"{indent_str}  condition:")
        lines.append(
            _format_ast_node(node.condition, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, AssertElseNode):
        lines = [f"{indent_str}AssertElseNode("]
        lines.append(f"{indent_str}  condition:")
        lines.append(
            _format_ast_node(node.condition, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str}  else:")
        lines.append(
            _format_ast_node(node.else_branch, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, WhileNode):
        lines = [f"{indent_str}WhileNode("]
        lines.append(f"{indent_str}  condition:")
        lines.append(
            _format_ast_node(node.condition, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str}  body:")
        lines.append(
            _format_ast_node(node.body, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, ForNode):
        lines = [f"{indent_str}ForNode("]
        lines.append(f"{indent_str}  iterator={repr(node.iterator)}")
        lines.append(f"{indent_str}  body:")
        lines.append(
            _format_ast_node(node.body, indent + 4, max_depth, current_depth + 1)
        )
        lines.append(f"{indent_str})")
        return "\n".join(lines)

    elif isinstance(node, AtNode):
        return f"{indent_str}AtNode(levels={node.levels})"

    else:
        # Fallback for unknown node types
        return f"{indent_str}{node.__class__.__name__}({node})"


def pretty_print_ast(
    node: ASTNode, max_depth: Optional[int] = None, compact: bool = False
) -> str:
    """Format an AST node in a tree-like format.

    Args:
        node: The root AST node to format
        max_depth: Maximum depth to traverse (None for unlimited)
        compact: If True, use more compact formatting

    Returns:
        A formatted string representation of the AST tree
    """
    if node is None:
        return "None"

    result = _format_ast_node(node, indent=0, max_depth=max_depth, current_depth=0)

    if compact:
        # Remove extra blank lines in compact mode
        lines = [line for line in result.split("\n") if line.strip()]
        return "\n".join(lines)

    return result
