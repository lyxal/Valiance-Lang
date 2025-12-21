import argparse

from valiance.parser.Errors import GenericParseError
from valiance.lexer.Scanner import Scanner
from valiance.parser.NewParser import Parser
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

        if parser_.errors:
            print("\033[91mThere were problems.\033[0m")

            global_errors: list[GenericParseError] = []

            for error_category, errors in parser_.errors:
                if error_category == "Global":
                    global_errors.extend(errors)
                    continue
                print(f"\033[93mErrors while parsing {error_category}:\033[0m")
                for error in errors:
                    print(f"  {error}")

            if global_errors:
                print(f"\033[93mGlobal Errors:\033[0m")
                for error in global_errors:
                    print(f"  {error}")

        if not asts:
            print("\033[91mNo AST generated.\033[0m")
            continue

        if parser_.errors:
            # Use a blue color to indicate partial success
            print("\033[94mPartial AST:\033[0m")

        for ast in asts:
            print(pretty_print_ast(ast))


if __name__ == "__main__":
    main()
