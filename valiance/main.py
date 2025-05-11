from bytecode.chunk import Chunk
from bytecode.interpreter import Interpreter
from bytecode.ops import OpCode


def main():
    testChunk: Chunk = Chunk()

    testChunk.write_push_int(69420)
    testChunk.write_byte(OpCode.DUP)
    testChunk.write_byte(OpCode.ADD)

    interpreter = Interpreter(testChunk.code)
    result = interpreter.run()
    print("Bytecode:")
    print(testChunk)
    print("Result:", result)


if __name__ == "__main__":
    main()
