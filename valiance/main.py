from valiance.lexer.Scanner import Scanner


def main():
    program = """0...5"""
    scanner = Scanner(program)
    tokens = scanner.scan_tokens()
    print(tokens)


if __name__ == "__main__":
    main()
