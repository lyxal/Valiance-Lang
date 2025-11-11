"""Pretty-printer utilities for lexer tokens.

This module provides functions to format Token objects in human-readable formats
for debugging and visualization purposes.
"""

from typing import Sequence
from valiance.lexer.Token import Token


def pretty_print_token(token: Token) -> str:
    """Format a single token with its type, value, and position information.
    
    Args:
        token: The token to format
        
    Returns:
        A formatted string representation of the token
    """
    token_type = token.type.name
    value_repr = repr(token.value) if token.value else "''"
    return f"{token_type:<15} {value_repr:<20} (L{token.line}:C{token.column})"


def pretty_print_tokens(tokens: Sequence[Token], compact: bool = False) -> str:
    """Format a list of tokens in a tabular format.
    
    Args:
        tokens: The list of tokens to format
        compact: If True, use a more compact output format
        
    Returns:
        A formatted string representation of all tokens
    """
    if not tokens:
        return "No tokens to display"
    
    if compact:
        # Compact format: one line per token without header
        lines = [pretty_print_token(token) for token in tokens]
        return "\n".join(lines)
    
    # Full tabular format with header
    lines = [
        "TOKEN TYPE      VALUE                POSITION",
        "-" * 60
    ]
    
    for token in tokens:
        lines.append(pretty_print_token(token))
    
    return "\n".join(lines)
