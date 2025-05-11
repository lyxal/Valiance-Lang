from bytecode.chunk import Chunk
from bytecode.ops import OpCode


def main():
    testChunk: Chunk = Chunk()
    testChunk.write_byte(OpCode.PUSH_INT_BYTE)
    testChunk.write_byte(0x01)
    testChunk.write_byte(OpCode.PUSH_INT_BYTE)
    testChunk.write_byte(0x02)
    testChunk.write_byte(OpCode.ADD)

    print(repr(testChunk))


if __name__ == "__main__":
    main()
