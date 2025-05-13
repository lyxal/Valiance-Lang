from enum import Enum


class Op(Enum):
    # Fundamental pushes

    PUSH_NUMBER = 0x00
    PUSH_BYTE = 0x01
    PUSH_DOUBLE_BYTE = 0x02
    PUSH_STRING = 0x03
    PUSH_LIST = 0x04
    PUSH_FUNCTION = 0x05

    # Basic stack manipulation

    DUMP_STACK = 0x06
    DUPLICATE = 0x07
    SWAP = 0x08
    POP = 0x09

    # IO

    PRINT = 0x0A
    INPUT = 0x0B
    PRINT_WITH_NEWLINE = 0x0C

    # Jumps

    JUMP_NON_ZERO = 0x0D
    JUMP_ZERO = 0x0E
    GOTO = 0x0F

    # Basic maths

    ADD = 0x10
