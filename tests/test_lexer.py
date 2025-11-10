from valiance.lexer.TokenType import TokenType
import valiance.lexer.Scanner as Scanner
import valiance.lexer.Token as Token

import pytest


def scan(source: str) -> list[Token.Token]:
    scanner = Scanner.Scanner(source)
    return scanner.scan_tokens()


def tokens_equal(t1: list[Token.Token], t2: list[tuple[TokenType, str]]) -> bool:
    if len(t1) != len(t2):
        return False
    for token1, token2 in zip(t1, t2):
        # Just compare type and value for simplicity
        # No need to compare line and column in this test
        if token1.type != token2[0] or token1.value != token2[1]:
            return False
    return True


def test_basic_number():
    assert tokens_equal(scan("123"), [(TokenType.NUMBER, "123"), (TokenType.EOF, "")])


def test_two_numbers():
    assert tokens_equal(
        scan("123 456"),
        [(TokenType.NUMBER, "123"), (TokenType.NUMBER, "456"), (TokenType.EOF, "")],
    )


def test_basic_decimal_number():
    assert tokens_equal(scan("1.23"), [(TokenType.NUMBER, "1.23"), (TokenType.EOF, "")])


def test_basic_imaginary_number():
    assert tokens_equal(
        scan("12i34"), [(TokenType.NUMBER, "12i34"), (TokenType.EOF, "")]
    )
    assert tokens_equal(scan("5i0"), [(TokenType.NUMBER, "5i0"), (TokenType.EOF, "")])
    assert tokens_equal(scan("0i5"), [(TokenType.NUMBER, "0i5"), (TokenType.EOF, "")])


def test_negative_number():
    assert tokens_equal(scan("-69"), [(TokenType.NUMBER, "-69"), (TokenType.EOF, "")])
    assert tokens_equal(
        scan("-3.14"), [(TokenType.NUMBER, "-3.14"), (TokenType.EOF, "")]
    )


def test_leading_0s():
    assert tokens_equal(
        scan("001"),
        [
            (TokenType.NUMBER, "0"),
            (TokenType.NUMBER, "0"),
            (TokenType.NUMBER, "1"),
            (TokenType.EOF, ""),
        ],
    )


def test_decimal_leading_0():
    assert tokens_equal(scan("0.5"), [(TokenType.NUMBER, "0.5"), (TokenType.EOF, "")])


def test_small_decimal_number():
    assert tokens_equal(
        scan("0.0005"), [(TokenType.NUMBER, "0.0005"), (TokenType.EOF, "")]
    )
    assert tokens_equal(scan("0.05"), [(TokenType.NUMBER, "0.05"), (TokenType.EOF, "")])


def test_imaginary_with_negatives():
    assert tokens_equal(
        scan("-3i-4"), [(TokenType.NUMBER, "-3i-4"), (TokenType.EOF, "")]
    )
    assert tokens_equal(scan("5i-6"), [(TokenType.NUMBER, "5i-6"), (TokenType.EOF, "")])
    assert tokens_equal(scan("-7i8"), [(TokenType.NUMBER, "-7i8"), (TokenType.EOF, "")])


def test_imaginary_decimal():
    assert tokens_equal(
        scan("2.5i3.5"), [(TokenType.NUMBER, "2.5i3.5"), (TokenType.EOF, "")]
    )
    assert tokens_equal(
        scan("-1.2i-3.4"), [(TokenType.NUMBER, "-1.2i-3.4"), (TokenType.EOF, "")]
    )
    assert tokens_equal(
        scan("0.0i0.0"), [(TokenType.NUMBER, "0.0i0.0"), (TokenType.EOF, "")]
    )
    assert tokens_equal(
        scan("3.14i-5.1"), [(TokenType.NUMBER, "3.14i-5.1"), (TokenType.EOF, "")]
    )
    assert tokens_equal(
        scan("-0.5i2.5"), [(TokenType.NUMBER, "-0.5i2.5"), (TokenType.EOF, "")]
    )


def test_invalid_numbers():
    with pytest.raises(ValueError):
        scan("12.34.56")  # Multiple decimal points

    with pytest.raises(ValueError):
        scan("0...5")  # Ellipsis should not be part of the number


def test_imaginary_followed_by_i():
    assert tokens_equal(
        scan("3i4i5"),
        [
            (TokenType.NUMBER, "3i4"),
            (
                TokenType.WORD,
                "i5",
            ),
            (TokenType.EOF, ""),
        ],
    )


def test_negative_at_the_end():
    assert tokens_equal(
        scan("5-"),
        [
            (TokenType.NUMBER, "5"),
            (TokenType.WORD, "-"),
            (TokenType.EOF, ""),
        ],
    )

    assert tokens_equal(
        scan("3-4"),
        [
            (TokenType.NUMBER, "3"),
            (TokenType.NUMBER, "-4"),
            (TokenType.EOF, ""),
        ],
    )

    assert tokens_equal(
        scan("3- 4"),
        [
            (TokenType.NUMBER, "3"),
            (TokenType.WORD, "-"),
            (TokenType.NUMBER, "4"),
            (TokenType.EOF, ""),
        ],
    )


def test_decimal_at_the_end():
    with pytest.raises(ValueError):
        scan("5.")  # Decimal point without following digits


def test_basic_string():
    assert tokens_equal(
        scan('"Hello, World!"'),
        [(TokenType.STRING, "Hello, World!"), (TokenType.EOF, "")],
    )


def test_unterminated_string():
    with pytest.raises(ValueError):
        scan('"This string is not terminated')  # Unterminated string


def test_string_with_escape_sequences():
    assert tokens_equal(
        scan(r'"Line1\nLine2\tTabbed\""'),
        [(TokenType.STRING, 'Line1\nLine2\tTabbed"'), (TokenType.EOF, "")],
    )


def test_string_with_literal_newline():
    assert tokens_equal(
        scan('"This is a\nmulti-line string"'),
        [(TokenType.STRING, "This is a\nmulti-line string"), (TokenType.EOF, "")],
    )


def test_empty_string():
    assert tokens_equal(scan('""'), [(TokenType.STRING, ""), (TokenType.EOF, "")])


def test_words():
    assert tokens_equal(scan("hello"), [(TokenType.WORD, "hello"), (TokenType.EOF, "")])
    assert tokens_equal(
        scan("var_name123"), [(TokenType.WORD, "var_name123"), (TokenType.EOF, "")]
    )


def test_empty_variable_name():
    with pytest.raises(ValueError):
        scan("$")  # Empty variable name


def test_variable_assignment():
    assert tokens_equal(
        scan("$var = 10"),
        [
            (TokenType.VARIABLE, "var"),
            (TokenType.EQUALS, "="),
            (TokenType.NUMBER, "10"),
            (TokenType.EOF, ""),
        ],
    )


def test_variable_retrieval():
    assert tokens_equal(
        scan("$myVar"),
        [(TokenType.VARIABLE, "myVar"), (TokenType.EOF, "")],
    )


def test_equals_sign():
    assert tokens_equal(
        scan("="),
        [(TokenType.EQUALS, "="), (TokenType.EOF, "")],
    )

    # == isn't a special token, it's a single WORD token
    assert tokens_equal(
        scan("=="),
        [(TokenType.WORD, "=="), (TokenType.EOF, "")],
    )


def test_variable_name_with_multiple_accessors():
    assert tokens_equal(
        scan("$obj.field.subfield"),
        [(TokenType.VARIABLE, "obj.field.subfield"), (TokenType.EOF, "")],
    )


def test_variable_name_with_underscores_and_digits():
    assert tokens_equal(
        scan("$var_name_123"),
        [(TokenType.VARIABLE, "var_name_123"), (TokenType.EOF, "")],
    )

    with pytest.raises(ValueError):
        scan("$67")  # Invalid variable name starting with a digit


def test_recognise_reserved_keywords():
    assert tokens_equal(
        scan("above async await parallel spawn concurrent"),
        [
            (TokenType.ABOVE, "above"),
            (TokenType.ASYNC, "async"),
            (TokenType.AWAIT, "await"),
            (TokenType.PARALLEL, "parallel"),
            (TokenType.SPAWN, "spawn"),
            (TokenType.CONCURRENT, "concurrent"),
            (TokenType.EOF, ""),
        ],
    )

    assert tokens_equal(
        scan(
            "define fn import match object trait variant private public readable self this"
        ),
        [
            (TokenType.DEFINE, "define"),
            (TokenType.FN, "fn"),
            (TokenType.IMPORT, "import"),
            (TokenType.MATCH, "match"),
            (TokenType.OBJECT, "object"),
            (TokenType.TRAIT, "trait"),
            (TokenType.VARIANT, "variant"),
            (TokenType.PRIVATE, "private"),
            (TokenType.PUBLIC, "public"),
            (TokenType.READABLE, "readable"),
            (TokenType.SELF, "self"),
            (TokenType.THIS, "this"),
            (TokenType.EOF, ""),
        ],
    )
