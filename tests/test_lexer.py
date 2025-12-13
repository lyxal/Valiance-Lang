from typing import Any, Tuple, cast
import pytest

import valiance.lexer.Scanner as Scanner
import valiance.lexer.Token as Token
from valiance.lexer.TokenType import TokenType

NEWLINE_TOKEN = (TokenType.NEWLINE, "\n")


class TokenStream:
    def __init__(self, tokens: list[Token.Token] | list[Tuple[TokenType, str]]):
        if not tokens:
            self.tokens = []
        elif isinstance(tokens[0], Token.Token):  # List of tokens
            self.tokens = cast(list[Token.Token], tokens)
            if self.tokens[-1].type == TokenType.EOF:
                self.tokens.pop()  # Remove EOF token for testing
        else:
            raw_tokens = cast(list[Tuple[TokenType, str]], tokens)
            self.tokens = [Token.Token(t, v, -1, -1) for (t, v) in raw_tokens]

    def __eq__(self, otherStream: Any) -> bool:
        if not isinstance(otherStream, TokenStream):
            return NotImplemented
        t1 = [token for token in self.tokens if token.type != TokenType.WHITESPACE]
        t2 = otherStream.tokens
        if len(t1) != len(t2):
            return False
        for token1, token2 in zip(t1, t2):
            # Just compare type and value for simplicity
            # No need to compare line and column in this test
            if token1.type != token2.type or token1.value != token2.value:
                return False
        return True

    def __repr__(self) -> str:
        return f"{self.tokens}"


def scan(source: str) -> TokenStream:
    scanner = Scanner.Scanner(source)
    return TokenStream(scanner.scan_tokens())


def test_simple_number():
    assert scan("123") == TokenStream([(TokenType.NUMBER, "123")])


def test_valid_decimal_number():
    assert scan("6.7") == TokenStream([(TokenType.NUMBER, "6.7")])
    assert scan("10.50") == TokenStream([(TokenType.NUMBER, "10.50")])


def test_leading_zero_decimal():
    assert scan("0.123") == TokenStream([(TokenType.NUMBER, "0.123")])
    assert scan("0.0") == TokenStream([(TokenType.NUMBER, "0.0")])


def test_invalid_decimal_number():
    with pytest.raises(ValueError):
        scan("123.")


def test_leading_zero_integer():
    assert scan("0123") == TokenStream(
        [(TokenType.NUMBER, "0"), (TokenType.NUMBER, "123")]
    )
    assert scan("0") == TokenStream([(TokenType.NUMBER, "0")])


def test_valid_imaginary_number():
    assert scan("3i1") == TokenStream([(TokenType.NUMBER, "3i1")])
    assert scan("4.5i0") == TokenStream([(TokenType.NUMBER, "4.5i0")])
    assert scan("0.123i5.3") == TokenStream([(TokenType.NUMBER, "0.123i5.3")])


def test_invalid_imaginary_number():
    with pytest.raises(ValueError):
        scan("3i")
    with pytest.raises(ValueError):
        scan("4.5i")
    with pytest.raises(ValueError):
        scan("0.123i5.")


def test_thing_that_look_imaginary_but_is_not():
    # This should not be treated as an imaginary number
    assert scan("i3") == TokenStream([(TokenType.WORD, "i3")])


def test_valid_exponential_number():
    assert scan("2e3") == TokenStream([(TokenType.NUMBER, "2e3")])
    assert scan("5.5e-2") == TokenStream([(TokenType.NUMBER, "5.5e-2")])
    assert scan("1.23e4.4") == TokenStream([(TokenType.NUMBER, "1.23e4.4")])


def test_invalid_exponential_number():
    with pytest.raises(ValueError):
        scan("2e")
    with pytest.raises(ValueError):
        scan("5.5e")
    with pytest.raises(ValueError):
        scan("1.23e4.")


def test_negative_number():
    assert scan("-123") == TokenStream([(TokenType.NUMBER, "-123")])
    assert scan("-0.456") == TokenStream([(TokenType.NUMBER, "-0.456")])
    assert scan("-3i2") == TokenStream([(TokenType.NUMBER, "-3i2")])
    assert scan("-4.5e-6") == TokenStream([(TokenType.NUMBER, "-4.5e-6")])
    assert scan("-0.0") == TokenStream([(TokenType.NUMBER, "-0.0")])
    assert scan("6i-7") == TokenStream([(TokenType.NUMBER, "6i-7")])
    assert scan("-2e-3") == TokenStream([(TokenType.NUMBER, "-2e-3")])


def test_invalid_negative_number():
    with pytest.raises(ValueError):
        scan("-0.")
    with pytest.raises(ValueError):
        scan("-3i")
    with pytest.raises(ValueError):
        scan("-4.5e")
    with pytest.raises(ValueError):
        scan("-0.123i5.")


def test_simple_string():
    assert scan('"hello"') == TokenStream([(TokenType.STRING, "hello")])


def test_string_with_escape():
    assert scan(
        '"I kid you not, he really said \\"6 7\\" and did the funny brainrot gesture"'
    ) == TokenStream(
        [
            (
                TokenType.STRING,
                'I kid you not, he really said "6 7" and did the funny brainrot gesture',
            )
        ]
    )


def test_unterminated_string():
    with pytest.raises(ValueError):
        scan('"This is an unterminated string')


def test_string_with_newline():
    assert scan('"This is a string\nwith a newline"') == TokenStream(
        [(TokenType.STRING, "This is a string\nwith a newline")]
    )


def test_comments_are_ignored():
    assert scan("#? This is a comment") == TokenStream([])
    assert scan("#?This is a comment\n123") == TokenStream(
        [NEWLINE_TOKEN, (TokenType.NUMBER, "123")]
    )
    assert scan("123 #? This is a comment") == TokenStream([(TokenType.NUMBER, "123")])
    assert scan("123\n#? Another comment") == TokenStream(
        [(TokenType.NUMBER, "123"), NEWLINE_TOKEN]
    )
    assert scan("#? Comment\n#? Another comment\n456") == TokenStream(
        [NEWLINE_TOKEN, NEWLINE_TOKEN, (TokenType.NUMBER, "456")]
    )


def test_multiline_comments():
    assert scan("#{This\nComment\nSpans\nMultiple\nLines}#") == TokenStream([])


def test_tag_token():
    assert scan("#tag") == TokenStream([(TokenType.TAG_TOKEN, "tag")])
    assert scan("#-tag") == TokenStream([(TokenType.TAG_TOKEN, "-tag")])


def test_invalid_tag_token():
    with pytest.raises(ValueError):
        scan("#")  # Missing tag name
    with pytest.raises(ValueError):
        scan("#-")  # Missing tag name after '-'


def test_word_tokens():
    assert scan("variable_name") == TokenStream([(TokenType.WORD, "variable_name")])
    assert scan("fn myFunction") == TokenStream(
        [(TokenType.FN, "fn"), (TokenType.WORD, "myFunction")]
    )


def test_variable_get():
    assert scan("$variable") == TokenStream([(TokenType.VARIABLE, "variable")])
    assert scan("$var123_name") == TokenStream([(TokenType.VARIABLE, "var123_name")])


def test_invalid_variable_get():
    with pytest.raises(ValueError):
        scan("$")  # Missing variable name
    with pytest.raises(ValueError):
        scan("$123var")  # Invalid variable name starting with a digit


def test_single_equals():
    assert scan("=") == TokenStream([(TokenType.EQUALS, "=")])
    assert scan("$x = $y") == TokenStream(
        [(TokenType.VARIABLE, "x"), (TokenType.EQUALS, "="), (TokenType.VARIABLE, "y")]
    )


def test_double_equals():
    assert scan("==") == TokenStream([(TokenType.WORD, "==")])
