from lexer.Lexer import Lexer


def main():
    while True:
        text = ""
        try:
            text = input("valiance> ")
        except EOFError:
            break
        if not text:
            continue
        tokens = Lexer.tokenise(text)
        for token in tokens:
            print(token)

if __name__ == "__main__":
    main()
