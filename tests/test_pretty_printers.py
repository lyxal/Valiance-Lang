"""Tests for pretty-printer utilities."""

import pytest

from valiance.lexer.PrettyPrinter import (pretty_print_token,
                                          pretty_print_tokens)
from valiance.lexer.Token import Token
from valiance.lexer.TokenType import TokenType
from valiance.parser.AST import (DefineNode, ElementNode, GroupNode, IfNode,
                                 ListNode, LiteralNode, TupleNode, TypeNode,
                                 VariableGetNode, VariableSetNode)
from valiance.parser.PrettyPrinter import pretty_print_ast
from valiance.vtypes.VTypes import NumberType, StringType


class TestLexerPrettyPrinter:
    """Tests for lexer pretty-printer functions."""

    def test_pretty_print_token_basic(self):
        """Test pretty printing a single token."""
        token = Token(TokenType.NUMBER, "123", 1, 5)
        result = pretty_print_token(token)
        assert "NUMBER" in result
        assert "'123'" in result
        assert "L1:C5" in result

    def test_pretty_print_token_empty_value(self):
        """Test pretty printing a token with empty value."""
        token = Token(TokenType.EOF, "", 1, 10)
        result = pretty_print_token(token)
        assert "EOF" in result
        assert "''" in result
        assert "L1:C10" in result

    def test_pretty_print_tokens_empty_list(self):
        """Test pretty printing an empty token list."""
        result = pretty_print_tokens([])
        assert result == "No tokens to display"

    def test_pretty_print_tokens_single_token(self):
        """Test pretty printing a single token in a list."""
        tokens = [Token(TokenType.WORD, "hello", 1, 1)]
        result = pretty_print_tokens(tokens)
        assert "TOKEN TYPE" in result
        assert "VALUE" in result
        assert "POSITION" in result
        assert "WORD" in result
        assert "'hello'" in result

    def test_pretty_print_tokens_multiple_tokens(self):
        """Test pretty printing multiple tokens."""
        tokens = [
            Token(TokenType.DEFINE, "define", 1, 1),
            Token(TokenType.WORD, "add", 1, 8),
            Token(TokenType.NUMBER, "42", 2, 1),
        ]
        result = pretty_print_tokens(tokens)
        assert "DEFINE" in result
        assert "WORD" in result
        assert "NUMBER" in result
        assert "'define'" in result
        assert "'add'" in result
        assert "'42'" in result

    def test_pretty_print_tokens_compact(self):
        """Test compact mode for token printing."""
        tokens = [
            Token(TokenType.NUMBER, "1", 1, 1),
            Token(TokenType.NUMBER, "2", 1, 3),
        ]
        result = pretty_print_tokens(tokens, compact=True)
        # Compact mode should not include header
        assert "TOKEN TYPE" not in result
        assert "NUMBER" in result
        assert "'1'" in result
        assert "'2'" in result


class TestParserPrettyPrinter:
    """Tests for parser pretty-printer functions."""

    def test_pretty_print_ast_none(self):
        """Test pretty printing None."""
        result = pretty_print_ast(None)
        assert result == "None"

    def test_pretty_print_literal_node(self):
        """Test pretty printing a LiteralNode."""
        node = LiteralNode(value="42", type_=NumberType())
        result = pretty_print_ast(node)
        assert "LiteralNode" in result
        assert "'42'" in result
        assert "NumberType" in result

    def test_pretty_print_variable_get_node(self):
        """Test pretty printing a VariableGetNode."""
        node = VariableGetNode(name="x")
        result = pretty_print_ast(node)
        assert "VariableGetNode" in result
        assert "'x'" in result

    def test_pretty_print_group_node_empty(self):
        """Test pretty printing an empty GroupNode."""
        node = GroupNode(elements=[])
        result = pretty_print_ast(node)
        assert "GroupNode" in result
        assert "[]" in result

    def test_pretty_print_group_node_with_elements(self):
        """Test pretty printing a GroupNode with elements."""
        node = GroupNode(
            elements=[
                LiteralNode(value="1", type_=NumberType()),
                LiteralNode(value="2", type_=NumberType()),
            ]
        )
        result = pretty_print_ast(node)
        assert "GroupNode" in result
        assert "LiteralNode" in result
        assert "'1'" in result
        assert "'2'" in result

    def test_pretty_print_element_node_simple(self):
        """Test pretty printing a simple ElementNode."""
        node = ElementNode(element_name="add", generics=[], args=[], modified=False)
        result = pretty_print_ast(node)
        assert "ElementNode" in result
        assert "'add'" in result

    def test_pretty_print_element_node_with_args(self):
        """Test pretty printing an ElementNode with arguments."""
        node = ElementNode(
            element_name="func",
            generics=[],
            args=[
                ("x", LiteralNode(value="10", type_=NumberType())),
            ],
            modified=False,
        )
        result = pretty_print_ast(node)
        assert "ElementNode" in result
        assert "'func'" in result
        assert "'x'" in result
        assert "'10'" in result

    def test_pretty_print_tuple_node(self):
        """Test pretty printing a TupleNode."""
        node = TupleNode(
            elements=[
                LiteralNode(value="a", type_=StringType()),
                LiteralNode(value="b", type_=StringType()),
            ]
        )
        result = pretty_print_ast(node)
        assert "TupleNode" in result
        assert "LiteralNode" in result
        assert "'a'" in result
        assert "'b'" in result

    def test_pretty_print_type_node(self):
        """Test pretty printing a TypeNode."""
        node = TypeNode(type_="Int")
        result = pretty_print_ast(node)
        assert "TypeNode" in result
        assert "'Int'" in result

    def test_pretty_print_define_node(self):
        """Test pretty printing a DefineNode."""
        node = DefineNode(
            generics=[],
            name="square",
            parameters=[("n", TypeNode(type_="Int"))],
            output=[TypeNode(type_="Int")],
            body=GroupNode(
                elements=[
                    VariableGetNode(name="n"),
                ]
            ),
        )
        result = pretty_print_ast(node)
        assert "DefineNode" in result
        assert "'square'" in result
        assert "'n'" in result
        assert "'Int'" in result
        assert "body:" in result
        assert "GroupNode" in result

    def test_pretty_print_variable_set_node(self):
        """Test pretty printing a VariableSetNode."""
        node = VariableSetNode(
            name="x", value=LiteralNode(value="5", type_=NumberType())
        )
        result = pretty_print_ast(node)
        assert "VariableSetNode" in result
        assert "'x'" in result
        assert "value:" in result
        assert "LiteralNode" in result
        assert "'5'" in result

    def test_pretty_print_list_node(self):
        """Test pretty printing a ListNode."""
        node = ListNode(
            items=[
                LiteralNode(value="1", type_=NumberType()),
                LiteralNode(value="2", type_=NumberType()),
                LiteralNode(value="3", type_=NumberType()),
            ]
        )
        result = pretty_print_ast(node)
        assert "ListNode" in result
        assert "LiteralNode" in result
        assert "'1'" in result
        assert "'2'" in result
        assert "'3'" in result

    def test_pretty_print_if_node(self):
        """Test pretty printing an IfNode."""
        node = IfNode(
            condition=GroupNode(
                elements=[LiteralNode(value="true", type_=StringType())]
            ),
            then_branch=GroupNode(
                elements=[LiteralNode(value="42", type_=NumberType())]
            ),
        )
        result = pretty_print_ast(node)
        assert "IfNode" in result
        assert "condition:" in result
        assert "then:" in result
        assert "GroupNode" in result

    def test_pretty_print_ast_with_max_depth(self):
        """Test pretty printing with max depth limit."""
        node = GroupNode(
            elements=[
                GroupNode(
                    elements=[
                        GroupNode(
                            elements=[LiteralNode(value="deep", type_=StringType())]
                        )
                    ]
                )
            ]
        )
        result = pretty_print_ast(node, max_depth=2)
        assert "GroupNode" in result
        assert "[...]" in result

    def test_pretty_print_ast_compact(self):
        """Test compact mode for AST printing."""
        node = GroupNode(
            elements=[
                LiteralNode(value="1", type_=NumberType()),
            ]
        )
        result = pretty_print_ast(node, compact=True)
        assert "GroupNode" in result
        assert "LiteralNode" in result
        # Compact mode removes extra blank lines
        lines = result.split("\n")
        assert all(line.strip() for line in lines)
