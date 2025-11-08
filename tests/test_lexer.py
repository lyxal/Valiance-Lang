import valiance.lexer.Scanner as Scanner
import valiance.lexer.Token as Token


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


def test_negative_number():
    assert tokens_equal(scan("-69"), [(Token.TokenType.NUMBER, "-69")])


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
