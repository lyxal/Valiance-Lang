import argparse
import logging
import pathlib
import os

from valiance.analysis.Analyser import Analyser
from valiance.parser.AST import AuxiliaryNode, GroupNode
from valiance.parser.Errors import GenericParseError
from valiance.lexer.Scanner import Scanner
from valiance.parser.Parser import Parser
from valiance.parser.PrettyPrinter import pretty_print_ast

from valiance.loglib.logging_config import setup_logging

# AST graph output
from valiance.parser.ast_viz import ast_to_dot, write_dot, render_with_graphviz
from valiance.compiler_common.Location import Location

logger = logging.getLogger(__name__)

BASE_DIR = pathlib.Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="Valiance compiler")

    # Pipeline stages (mutually exclusive)
    pipeline = parser.add_mutually_exclusive_group()
    pipeline.add_argument(
        "--lex-only", "-l", action="store_true", help="Run lexer only"
    )
    pipeline.add_argument(
        "--parse-only", "-p", action="store_true", help="Run lexer + parser only"
    )
    pipeline.add_argument(
        "--analyze-only",
        "-a",
        action="store_true",
        help="Run lexer + parser + static analysis only",
    )

    # Input source
    parser.add_argument("--file", "-f", type=str, help="Read code from specified file")
    parser.add_argument(
        "--test",
        "-t",
        action="store_true",
        help="Read code from sample.vlnc (for quick testing)",
    )

    # Output options
    parser.add_argument(
        "--svg",
        "-s",
        action="store_true",
        help="Generate DOT and render SVG of the AST",
    )
    parser.add_argument(
        "--svg-out",
        default="ast.svg",
        help="Output path for SVG file (default: ast.svg)",
    )
    parser.add_argument(
        "--open-svg",
        "-o",
        action="store_true",
        help="Open the generated SVG after rendering (requires --svg)",
    )
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty print the AST (when using parser)"
    )

    # Logging
    parser.add_argument(
        "--log",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)",
    )

    args = parser.parse_args()

    setup_logging(args.log)
    logger = logging.getLogger(__name__)
    logger.info("Application started")

    # Determine input source
    if args.test and args.file:
        logger.error("Cannot specify both --test and --file")
        return

    if args.test:
        input_file = BASE_DIR / "sample.vlnc"
    elif args.file:
        input_file = pathlib.Path(args.file)
    else:
        input_file = None

    # Determine pipeline stage (default to furthest implemented)
    run_lex_only = args.lex_only
    run_parse_only = args.parse_only
    run_analyze_only = args.analyze_only

    # If no pipeline flags given, run the full implemented pipeline
    if not (run_lex_only or run_parse_only or run_analyze_only):
        run_analyze_only = True

    # Main loop (REPL if no file, single run if file)
    while True:
        try:
            if input_file:
                with open(input_file, "r", encoding="utf-8") as f:
                    source = f.read()
            else:
                source = input(">> ")
        except EOFError:
            break
        except FileNotFoundError:
            logger.error(f"File not found: {input_file}")
            break

        # Lexer
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        if run_lex_only:
            for token in tokens:
                print(token)
            if input_file:
                break
            continue

        # Parser
        parser_ = Parser(tokens)
        asts = parser_.parse()

        # Print errors
        if parser_.errors:
            print("\033[91mThere were problems.\033[0m")
            _print_parser_errors(parser_.errors)

        if not asts:
            print("\033[91mNo AST generated.\033[0m")
            if input_file:
                break
            continue

        # Generate SVG if requested
        if args.svg:
            _generate_svg(asts, args.svg_out, args.open_svg)

        # Print AST if we're stopping at parse stage
        if run_parse_only:
            if parser_.errors:
                print("\033[94mPartial AST:\033[0m")

            if args.pretty:
                for ast in asts:
                    if isinstance(ast, AuxiliaryNode):
                        continue
                    print(pretty_print_ast(ast))
            else:
                for ast in asts:
                    print(ast)

            if input_file:
                break
            continue

        # Static Analysis
        if run_analyze_only:
            analyser = Analyser(asts)
            print(analyser.analyse())

        print("\033[93mFull pipeline not yet implemented.\033[0m")

        if input_file:
            break


def _print_parser_errors(errors):
    """Print parser errors in a formatted way."""
    global_errors: list[GenericParseError] = []

    for error_category, error_list in errors:
        if error_category == "Global":
            global_errors.extend(error_list)
            continue
        print(f"\033[93mErrors while parsing {error_category}:\033[0m")
        for error in error_list:
            print(f"  {error}")

    if global_errors:
        print(f"\033[93mGlobal Errors:\033[0m")
        for error in global_errors:
            print(f"  {error}")


def _generate_svg(asts, svg_path_str, open_after):
    """Generate DOT and render SVG from AST."""
    root = GroupNode(Location(-1, -1), asts)
    dot_text = ast_to_dot(root)

    svg_path = pathlib.Path(svg_path_str)
    dot_path = svg_path.with_suffix(".dot")

    # Write DOT
    write_dot(dot_text, dot_path)
    print(f"Wrote DOT to: {dot_path.resolve()}")

    # Render SVG
    try:
        render_with_graphviz(dot_path, svg_path, fmt="svg")
        print(f"Wrote SVG to: {svg_path.resolve()}")

        if open_after:
            os.startfile(svg_path)  # type: ignore[attr-defined]
    except Exception as e:
        print(f"\033[91mFailed to render SVG: {e}\033[0m")


if __name__ == "__main__":
    main()
