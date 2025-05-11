from enum import Enum


class OpCode(Enum):
    POP = 0x03
    DUP = 0x04
    SWAP = 0x05
    PRINT = 0x09
    PUSH_INT = 0x10
    PUSH_INT_BYTE = 0x11
    PUSH_INT_BYTE_2 = 0x12
    ADD = 0x20
