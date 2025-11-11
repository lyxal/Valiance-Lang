import valiance.parser.PrettyPrinter
from valiance.lexer.Scanner import Scanner
from valiance.parser.Parser import Parser


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
            pretty = valiance.parser.PrettyPrinter.pretty_print_ast(ast)
            print(pretty)


if __name__ == "__main__":
    main()
