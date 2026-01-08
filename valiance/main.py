import argparse
import logging
import pathlib
import os

from valiance.parser.AST import AuxiliaryNode, GroupNode
from valiance.parser.Errors import GenericParseError
from valiance.lexer.Scanner import Scanner
from valiance.parser.Parser import Parser
from valiance.parser.PrettyPrinter import pretty_print_ast

from valiance.loglib.logging_config import setup_logging
from valiance.loglib.log_block import log_block

# AST graph output
from valiance.parser.ast_viz import ast_to_dot, write_dot, render_with_graphviz
from valiance.compiler_common.Location import Location

logger = logging.getLogger(__name__)

BASE_DIR = pathlib.Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lex", action="store_true", help="Run lexer only (skip parser)"
    )

    parser.add_argument(
        "--log",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )

    parser.add_argument(
        "--rawast", action="store_true", help="Disable pretty print for parser"
    )

    parser.add_argument(
        "--f", action="store_true", help="Read code from the file 'sample.vlnc'"
    )

    # Graphviz AST output options
    parser.add_argument(
        "--dot",
        action="store_true",
        help="Write Graphviz DOT output of the parsed AST (ast.dot by default)",
    )
    parser.add_argument(
        "--svg",
        action="store_true",
        help="Render SVG from DOT using Graphviz (requires dot.exe)",
    )
    parser.add_argument(
        "--dot-out",
        default="ast.dot",
        help="Output path for DOT file (default: ast.dot). SVG will use same base name.",
    )
    parser.add_argument(
        "--dot-exe",
        default=None,
        help=r"Path to Graphviz dot.exe (e.g. C:\Program Files\Graphviz\bin\dot.exe). "
        r"If omitted, we try to find 'dot' on PATH.",
    )
    parser.add_argument(
        "--open-svg",
        action="store_true",
        help="Open the generated SVG after rendering (Windows: uses os.startfile). Requires --svg.",
    )

    args = parser.parse_args()

    setup_logging(args.log)

    logger = logging.getLogger(__name__)
    logger.info("Application started")

    use_pretty = not args.rawast

    while True:
        try:
            if args.f:
                with open(BASE_DIR / "sample.vlnc", "r", encoding="utf-8") as f:
                    source = f.read()
            else:
                source = input(">> ")
        except EOFError:
            break

        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        if args.lex:
            for token in tokens:
                print(token)
            if args.f:
                break
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
            if args.f:
                break
            continue

        # Graph output (one graph for all top-level ASTs)
        if args.dot or args.svg:
            root = GroupNode(Location(-1, -1), asts)
            dot_text = ast_to_dot(root, show_locations=False)

            dot_path = pathlib.Path(args.dot_out)
            write_dot(dot_text, dot_path)
            print(f"Wrote DOT to: {dot_path.resolve()}")

            if args.svg:
                svg_path = dot_path.with_suffix(".svg")
                try:
                    render_with_graphviz(
                        dot_path,
                        svg_path,
                        fmt="svg",
                        dot_exe=args.dot_exe,
                    )
                    print(f"Wrote SVG to: {svg_path.resolve()}")

                    if args.open_svg:
                        # Windows (cmd/Explorer) friendly
                        os.startfile(svg_path)  # type: ignore[attr-defined]
                except Exception as e:
                    print(f"\033[91mFailed to render SVG with Graphviz: {e}\033[0m")

        if parser_.errors:
            # Use a blue color to indicate partial success
            print("\033[94mPartial AST:\033[0m")

        if use_pretty:
            for ast in asts:
                if isinstance(ast, AuxiliaryNode):
                    continue
                print(pretty_print_ast(ast))
        else:
            for ast in asts:
                print(ast)

        if args.f:
            break


if __name__ == "__main__":
    main()
