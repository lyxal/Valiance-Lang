from bytecode.ops import OpCode
from bytecode.utils import decode_multibyte, encode_multibyte, merge_bytes


class Chunk:
    def __init__(self):
        self.code: list[int] = []

    def write_byte(self, byte: int | OpCode) -> None:
        match byte:
            case OpCode():
                self.code.append(byte.value)
            case int():
                self.code.append(byte)
            case _:
                raise TypeError(f"Expected int or OpCode, got {type(byte)}")

    def __repr__(self) -> str:
        output: str = ""
        offset: int = 0

        while offset < len(self.code):
            instruction: int = self.code[offset]
            match instruction:
                case OpCode.DUP.value:
                    output += f"{offset:04}: {OpCode.DUP.name}\n"
                    offset += 1
                case OpCode.POP.value:
                    output += f"{offset:04}: {OpCode.POP.name}\n"
                    offset += 1
                case OpCode.SWAP.value:
                    output += f"{offset:04}: {OpCode.SWAP.name}\n"
                    offset += 1
                case OpCode.PRINT.value:
                    output += f"{offset:04}: {OpCode.PRINT.name}\n"
                    offset += 1
                case OpCode.PUSH_INT.value:
                    bits: list[int] = []
                    offset += 1
                    while self.code[offset] & 128:
                        bits.append(self.code[offset])
                        offset += 1
                    bits.append(self.code[offset])
                    value = decode_multibyte(bits)
                    output += f"{offset:04}: {OpCode.PUSH_INT.name} {value}\n"
                    offset += 1
                case OpCode.PUSH_INT_BYTE.value:
                    output += f"{offset:04}: {OpCode.PUSH_INT_BYTE.name} {self.code[offset + 1]}\n"
                    offset += 2
                case OpCode.PUSH_INT_BYTE_2.value:
                    output += f"{offset:04}: {OpCode.PUSH_INT_BYTE_2.name} {merge_bytes(self.code[offset + 1:offset + 3])}\n"
                    offset += 3
                case OpCode.ADD.value:
                    output += f"{offset:04}: {OpCode.ADD.name}\n"
                    offset += 1
                case _:
                    output += f"{offset:04}: UNKNOWN INSTRUCTION {instruction}\n"
                    offset += 1
        return output

    def write_push_int(self, value: int) -> None:
        if value < 0x100:
            self.write_byte(OpCode.PUSH_INT_BYTE)
            self.write_byte(value)
        elif value < 0x10000:
            self.write_byte(OpCode.PUSH_INT_BYTE_2)
            self.write_byte(value >> 8)
            self.write_byte(value & 0xFF)
        else:
            self.write_byte(OpCode.PUSH_INT)
            # Write the value as a sequence of bytes, with the leading
            # bits set to 1 to indicate continuation

            self.code.extend(encode_multibyte(value))
