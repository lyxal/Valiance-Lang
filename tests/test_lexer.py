import valiance.lexer.Scanner as Scanner
import valiance.lexer.Token as Token


def scan(source: str) -> list[Token.Token]:
    scanner = Scanner.Scanner(source)
    return scanner.scan_tokens()


def tokens_equal(t1: list[Token.Token], t2: list[Token.Token]) -> bool:
    if len(t1) != len(t2):
        return False
    for token1, token2 in zip(t1, t2):
        # Just compare type and value for simplicity
        # No need to compare line and column in this test
        if token1.type != token2.type or token1.value != token2.value:
            return False
    return True


def test_numbers():
    assert tokens_equal(scan("123"), [Token.Token(Token.TokenType.NUMBER, "123", 1, 1)])
