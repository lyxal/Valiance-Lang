def repl():
    while True:
        line = input(">>> ")
        if line.strip() == "exit":
            break


def main():
    print("Welcome to the Valience REPL!")
    print("Type 'exit' to quit.")
    repl()


if __name__ == "__main__":
    main()
