import valiance.lexer.Scanner as Scanner
import valiance.lexer.Token as Token

import pytest


def scan(source: str) -> list[Token.Token]:
    scanner = Scanner.Scanner(source)
    return scanner.scan_tokens()


def tokens_equal(t1: list[Token.Token], t2: list[tuple[Token.TokenType, str]]) -> bool:
    if len(t1) != len(t2):
        return False
    for token1, token2 in zip(t1, t2):
        # Just compare type and value for simplicity
        # No need to compare line and column in this test
        if token1.type != token2[0] or token1.value != token2[1]:
            return False
    return True


def test_basic_number():
    assert tokens_equal(scan("123"), [(Token.TokenType.NUMBER, "123")])


def test_two_numbers():
    assert tokens_equal(
        scan("123 456"),
        [(Token.TokenType.NUMBER, "123"), (Token.TokenType.NUMBER, "456")],
    )


def test_basic_decimal_number():
    assert tokens_equal(scan("1.23"), [(Token.TokenType.NUMBER, "1.23")])


def test_basic_imaginary_number():
    assert tokens_equal(scan("12i34"), [(Token.TokenType.NUMBER, "12i34")])
    assert tokens_equal(scan("5i0"), [(Token.TokenType.NUMBER, "5i0")])
    assert tokens_equal(scan("0i5"), [(Token.TokenType.NUMBER, "0i5")])


def test_negative_number():
    assert tokens_equal(scan("-69"), [(Token.TokenType.NUMBER, "-69")])
    assert tokens_equal(scan("-3.14"), [(Token.TokenType.NUMBER, "-3.14")])


def test_leading_0s():
    assert tokens_equal(
        scan("001"),
        [
            (Token.TokenType.NUMBER, "0"),
            (Token.TokenType.NUMBER, "0"),
            (Token.TokenType.NUMBER, "1"),
        ],
    )


def test_decimal_leading_0():
    assert tokens_equal(scan("0.5"), [(Token.TokenType.NUMBER, "0.5")])


def test_small_decimal_number():
    assert tokens_equal(scan("0.0005"), [(Token.TokenType.NUMBER, "0.0005")])
    assert tokens_equal(scan("0.05"), [(Token.TokenType.NUMBER, "0.05")])


def test_imaginary_with_negatives():
    assert tokens_equal(scan("-3i-4"), [(Token.TokenType.NUMBER, "-3i-4")])
    assert tokens_equal(scan("5i-6"), [(Token.TokenType.NUMBER, "5i-6")])
    assert tokens_equal(scan("-7i8"), [(Token.TokenType.NUMBER, "-7i8")])


def test_imaginary_decimal():
    assert tokens_equal(scan("2.5i3.5"), [(Token.TokenType.NUMBER, "2.5i3.5")])
    assert tokens_equal(scan("-1.2i-3.4"), [(Token.TokenType.NUMBER, "-1.2i-3.4")])
    assert tokens_equal(scan("0.0i0.0"), [(Token.TokenType.NUMBER, "0.0i0.0")])
    assert tokens_equal(scan("3.14i-5.1"), [(Token.TokenType.NUMBER, "3.14i-5.1")])
    assert tokens_equal(scan("-0.5i2.5"), [(Token.TokenType.NUMBER, "-0.5i2.5")])


def test_invalid_numbers():
    with pytest.raises(ValueError):
        scan("12.34.56")  # Multiple decimal points

    with pytest.raises(ValueError):
        scan("0...5")  # Ellipsis should not be part of the number


def test_imaginary_followed_by_i():
    assert tokens_equal(
        scan("3i4i5"),
        [
            (Token.TokenType.NUMBER, "3i4"),
            (
                Token.TokenType.WORD,
                "i5",
            ),
        ],
    )


def test_negative_at_the_end():
    assert tokens_equal(
        scan("5-"),
        [
            (Token.TokenType.NUMBER, "5"),
            (Token.TokenType.WORD, "-"),
        ],
    )

    assert tokens_equal(
        scan("3-4"),
        [
            (Token.TokenType.NUMBER, "3"),
            (Token.TokenType.NUMBER, "-4"),
        ],
    )

    assert tokens_equal(
        scan("3- 4"),
        [
            (Token.TokenType.NUMBER, "3"),
            (Token.TokenType.WORD, "-"),
            (Token.TokenType.NUMBER, "4"),
        ],
    )


def test_decimal_at_the_end():
    with pytest.raises(ValueError):
        scan("5.")  # Decimal point without following digits


def test_basic_string():
    assert tokens_equal(
        scan('"Hello, World!"'), [(Token.TokenType.STRING, "Hello, World!")]
    )


def test_unterminated_string():
    with pytest.raises(ValueError):
        scan('"This string is not terminated')  # Unterminated string


def test_string_with_escape_sequences():
    assert tokens_equal(
        scan(r'"Line1\nLine2\tTabbed\""'),
        [(Token.TokenType.STRING, 'Line1\nLine2\tTabbed"')],
    )


def test_string_with_literal_newline():
    assert tokens_equal(
        scan('"This is a\nmulti-line string"'),
        [(Token.TokenType.STRING, "This is a\nmulti-line string")],
    )


def test_empty_string():
    assert tokens_equal(scan('""'), [(Token.TokenType.STRING, "")])


def test_words():
    assert tokens_equal(scan("hello"), [(Token.TokenType.WORD, "hello")])
    assert tokens_equal(scan("var_name123"), [(Token.TokenType.WORD, "var_name123")])


def test_empty_variable_name():
    with pytest.raises(ValueError):
        scan("$")  # Empty variable name


def test_variable_assignment():
    assert tokens_equal(
        scan("$var = 10"),
        [
            (Token.TokenType.VARIABLE, "var"),
            (Token.TokenType.EQUALS, "="),
            (Token.TokenType.NUMBER, "10"),
        ],
    )


def test_variable_retrieval():
    assert tokens_equal(
        scan("$myVar"),
        [(Token.TokenType.VARIABLE, "myVar")],
    )


def test_equals_sign():
    assert tokens_equal(
        scan("="),
        [(Token.TokenType.EQUALS, "=")],
    )

    # == isn't a special token, it's a single WORD token
    assert tokens_equal(
        scan("=="),
        [(Token.TokenType.WORD, "==")],
    )


def test_variable_name_with_multiple_accessors():
    assert tokens_equal(
        scan("$obj.field.subfield"),
        [(Token.TokenType.VARIABLE, "obj.field.subfield")],
    )


def test_variable_name_with_underscores_and_digits():
    assert tokens_equal(
        scan("$var_name_123"),
        [(Token.TokenType.VARIABLE, "var_name_123")],
    )

    with pytest.raises(ValueError):
        scan("$67")  # Invalid variable name starting with a digit


def test_recognise_reserved_keywords():
    assert tokens_equal(
        scan("above async await parallel spawn concurrent"),
        [
            (Token.TokenType.ABOVE, "above"),
            (Token.TokenType.ASYNC, "async"),
            (Token.TokenType.AWAIT, "await"),
            (Token.TokenType.PARALLEL, "parallel"),
            (Token.TokenType.SPAWN, "spawn"),
            (Token.TokenType.CONCURRENT, "concurrent"),
        ],
    )

    assert tokens_equal(
        scan(
            "define fn import match object trait variant private public readable self this"
        ),
        [
            (Token.TokenType.DEFINE, "define"),
            (Token.TokenType.FN, "fn"),
            (Token.TokenType.IMPORT, "import"),
            (Token.TokenType.MATCH, "match"),
            (Token.TokenType.OBJECT, "object"),
            (Token.TokenType.TRAIT, "trait"),
            (Token.TokenType.VARIANT, "variant"),
            (Token.TokenType.PRIVATE, "private"),
            (Token.TokenType.PUBLIC, "public"),
            (Token.TokenType.READABLE, "readable"),
            (Token.TokenType.SELF, "self"),
            (Token.TokenType.THIS, "this"),
        ],
    )
