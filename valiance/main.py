from lexer.Scanner import Scanner


def main():
    program = """$x = 5"""
    scanner = Scanner(program)
    tokens = scanner.scan_tokens()
    print(tokens)


if __name__ == "__main__":
    main()
