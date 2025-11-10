from valiance.parser.Parser import Parser
from valiance.lexer.Scanner import Scanner


def main():
    program = """$x: {2}"""
    scanner = Scanner(program)
    tokens = scanner.scan_tokens()

    parser = Parser(tokens)
    asts = parser.parse()
    print(asts)


if __name__ == "__main__":
    main()
