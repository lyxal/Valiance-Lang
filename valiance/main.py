from bytecode.chunk import Chunk
from bytecode.interpreter import Interpreter
from bytecode.ops import OpCode


def main():
    testChunk: Chunk = Chunk()

    testChunk.write_push_string("Hello, World!")
    testChunk.write_byte(OpCode.PRINT)

    print("Bytecode:")
    print(testChunk)

    interpreter = Interpreter(testChunk.code)
    result = interpreter.run()

    print("Result:", result)


if __name__ == "__main__":
    main()
