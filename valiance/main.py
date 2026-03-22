import valiance.lexer as lexer


def repl():
    while True:
        line = input(">>> ")
        if line.strip() == "exit":
            break
        tokens = lexer.Lexer(line).scan_tokens()
        for token in tokens:
            print(token)


def main():
    print("Welcome to the Valience REPL!")
    print("Type 'exit' to quit.")
    repl()


if __name__ == "__main__":
    main()
