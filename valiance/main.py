from vm.Interpreter import Interpreter


def main():
    interpreter = Interpreter()
    interpreter.run([0x01, 0x03, 0x01, 0x04, 0x06])


if __name__ == "__main__":
    main()
