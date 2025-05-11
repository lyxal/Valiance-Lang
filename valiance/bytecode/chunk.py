from bytecode.ops import OpCode


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
                case OpCode.PUSH_INT_BYTE.value:
                    output += f"{offset:04}: {OpCode.PUSH_INT_BYTE.name} {self.code[offset + 1]}\n"
                    offset += 2
                case OpCode.ADD.value:
                    output += f"{offset:04}: {OpCode.ADD.name}\n"
                    offset += 1
                case _:
                    output += f"{offset:04}: UNKNOWN INSTRUCTION {instruction}\n"
                    offset += 1
        return output
