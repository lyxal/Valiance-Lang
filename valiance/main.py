import argparse

import valiance.parser.PrettyPrinter
from valiance.lexer.Scanner import Scanner
from valiance.parser.Parser import Parser


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

        for ast in asts:
            pretty = valiance.parser.PrettyPrinter.pretty_print_ast(ast)
            print(pretty)


if __name__ == "__main__":
    main()
