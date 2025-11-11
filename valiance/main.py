from valiance.parser.Parser import Parser
from valiance.lexer.Scanner import Scanner


def main():
    while True:
        try:
            source = input(">> ")
        except EOFError:
            break

        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        parser = Parser(tokens)
        asts = parser.parse()

        for ast in asts:
            print(ast)


if __name__ == "__main__":
    main()
