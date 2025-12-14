import argparse

from valiance.parser.Errors import GenericParseError
from valiance.lexer.Scanner import Scanner
from valiance.parser.Parser import Parser
from valiance.parser.PrettyPrinter import pretty_print_ast


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lex", action="store_true", help="Run lexer only (skip parser)"
    )
    args = parser.parse_args()

    while True:
        try:
            source = input(">> ")
        except EOFError:
            break

        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        if args.lex:
            for token in tokens:
                print(token)
            continue

        parser_ = Parser(tokens)
        asts = parser_.parse()

        if asts and isinstance(asts[0], GenericParseError):
            print("Parsing errors:")
            for error in asts:
                print(error)
            continue

        for ast in asts:
            print(pretty_print_ast(ast))


if __name__ == "__main__":
    main()
