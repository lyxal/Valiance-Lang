from bytecode.ops import OpCode
from bytecode.utils import decode_multibyte, encode_multibyte, merge_bytes


class Chunk:
    def __init__(self):
        self.code: list[int] = []
        self.offset: int = 0

    def write_byte(self, byte: int | OpCode) -> None:
        match byte:
            case OpCode():
                self.code.append(byte.value)
            case int():
                self.code.append(byte)
            case _:
                raise TypeError(f"Expected int or OpCode, got {type(byte)}")

    def scan_multibyte(self) -> list[int]:
        bits: list[int] = []
        while self.code[self.offset] & 128:
            bits.append(self.code[self.offset])
            self.offset += 1
        bits.append(self.code[self.offset])
        return bits

    def __repr__(self) -> str:
        output: str = ""
        self.offset: int = 0

        while self.offset < len(self.code):
            instruction: int = self.code[self.offset]
            match instruction:
                case OpCode.ELEMENT.value:
                    self.offset += 1
                    element_address: int = decode_multibyte(self.scan_multibyte())
                    output += (
                        f"{self.offset:04}: {OpCode.ELEMENT.name} @ {element_address}\n"
                    )
                    self.offset += 1
                case OpCode.ELEMENT_B1.value:
                    self.offset += 1
                    element_address: int = self.code[self.offset]
                    output += f"{self.offset:04}: {OpCode.ELEMENT_B1.name} @ {element_address}\n"
                    self.offset += 1
                case OpCode.VEC_ELEMENT.value:
                    self.offset += 1
                    element_address: int = decode_multibyte(self.scan_multibyte())
                    output += f"{self.offset:04}: {OpCode.VEC_ELEMENT.name} @ {element_address}\n"
                    self.offset += 1
                case OpCode.DUP.value:
                    output += f"{self.offset:04}: {OpCode.DUP.name}\n"
                    self.offset += 1
                case OpCode.POP.value:
                    output += f"{self.offset:04}: {OpCode.POP.name}\n"
                    self.offset += 1
                case OpCode.SWAP.value:
                    output += f"{self.offset:04}: {OpCode.SWAP.name}\n"
                    self.offset += 1
                case OpCode.JMP.value:
                    self.offset += 1
                    jump_address: int = decode_multibyte(self.scan_multibyte())
                    output += f"{self.offset:04}: {OpCode.JMP.name} -> {jump_address}\n"
                    self.offset += 1
                case OpCode.JMP_B1.value:
                    self.offset += 1
                    jump_address: int = self.code[self.offset]
                    output += (
                        f"{self.offset:04}: {OpCode.JMP_B1.name} -> {jump_address}\n"
                    )
                    self.offset += 1
                case OpCode.VEC_ELEMENT_B1.value:
                    self.offset += 1
                    element_address: int = self.code[self.offset]
                    output += f"{self.offset:04}: {OpCode.VEC_ELEMENT_B1.name} @ {element_address}\n"
                    self.offset += 1
                case OpCode.PRINT.value:
                    output += f"{self.offset:04}: {OpCode.PRINT.name}\n"
                    self.offset += 1
                case OpCode.JNZ.value:
                    self.offset += 1
                    jump_address: int = decode_multibyte(self.scan_multibyte())
                    output += f"{self.offset:04}: {OpCode.JNZ.name} -> {jump_address}\n"
                    self.offset += 1
                case OpCode.JZ.value:
                    self.offset += 1
                    jump_address: int = decode_multibyte(self.scan_multibyte())
                    output += f"{self.offset:04}: {OpCode.JZ.name} -> {jump_address}\n"
                    self.offset += 1
                case OpCode.ENTER_FUNC.value:
                    self.offset += 1
                    function_address: int = decode_multibyte(self.scan_multibyte())
                    output += f"{self.offset:04}: {OpCode.ENTER_FUNC.name} @ {function_address}\n"
                    self.offset += 1
                case OpCode.EXIT_FUNC.value:
                    output += f"{self.offset:04}: {OpCode.EXIT_FUNC.name}\n"
                    self.offset += 1
                case OpCode.PUSH_INT.value:
                    self.offset += 1
                    value: int = decode_multibyte(self.scan_multibyte())
                    output += f"{self.offset:04}: {OpCode.PUSH_INT.name} {value}\n"
                    self.offset += 1
                case OpCode.PUSH_INT_BYTE.value:
                    output += f"{self.offset:04}: {OpCode.PUSH_INT_BYTE.name} {self.code[self.offset + 1]}\n"
                    self.offset += 2
                case OpCode.PUSH_INT_BYTE_2.value:
                    output += f"{self.offset:04}: {OpCode.PUSH_INT_BYTE_2.name} {merge_bytes(self.code[self.offset + 1:self.offset + 3])}\n"
                    self.offset += 3
                case OpCode.LOAD_CONST.value:
                    self.offset += 1
                    const_address: int = decode_multibyte(self.scan_multibyte())
                    output += f"{self.offset:04}: {OpCode.LOAD_CONST.name} @ {const_address}\n"
                    self.offset += 1
                case OpCode.DUMP_STACK.value:
                    output += f"{self.offset:04}: {OpCode.DUMP_STACK.name}\n"
                    self.offset += 1
                case OpCode.PUSH_STRING.value:
                    self.offset += 1
                    string_length = decode_multibyte(self.scan_multibyte())
                    # Get the next string_length bytes
                    self.offset += 1
                    string_bytes = self.code[self.offset : self.offset + string_length]
                    string_value = bytearray(string_bytes).decode("utf-8")
                    # Make sure to escape any single quotes in the string
                    string_value = string_value.replace("'", "\\'")
                    output += f"{self.offset:04}: {OpCode.PUSH_STRING.name} '{string_value}'\n"
                    self.offset += string_length
                    self.offset += 1
                case OpCode.PUSH_LIST.value:
                    # Don't show the whole list, just the length
                    self.offset += 1
                    list_length = decode_multibyte(self.scan_multibyte())
                    output += f"{self.offset:04}: {OpCode.PUSH_LIST.name} [{list_length} item(s)]\n"
                case OpCode.CREATE_OBJECT.value:
                    output += f"{self.offset:04}: {OpCode.CREATE_OBJECT.name}\n"
                    self.offset += 1
                case OpCode.PUSH_TYPE.value:
                    self.offset += 1
                    type_address: int = decode_multibyte(self.scan_multibyte())
                    output += (
                        f"{self.offset:04}: {OpCode.PUSH_TYPE.name} @ {type_address}\n"
                    )
                    self.offset += 1
                case OpCode.INPUT.value:
                    output += f"{self.offset:04}: {OpCode.INPUT.name}\n"
                    self.offset += 1
                case OpCode.PUSH_TYPE_B1.value:
                    self.offset += 1
                    type_address: int = self.code[self.offset]
                    output += f"{self.offset:04}: {OpCode.PUSH_TYPE_B1.name} @ {type_address}\n"
                    self.offset += 1
                case OpCode.GET_FIELD.value:
                    self.offset += 1
                    field_address: int = decode_multibyte(self.scan_multibyte())
                    output += (
                        f"{self.offset:04}: {OpCode.GET_FIELD.name} @ {field_address}\n"
                    )
                    self.offset += 1

                case OpCode.SET_FIELD.value:
                    self.offset += 1
                    field_address: int = decode_multibyte(self.scan_multibyte())
                    output += (
                        f"{self.offset:04}: {OpCode.SET_FIELD.name} @ {field_address}\n"
                    )
                    self.offset += 1
                case OpCode.DEBUG.value:
                    output += f"{self.offset:04}: {OpCode.DEBUG.name}\n"
                    self.offset += 1
                case OpCode.PUSH_FUNCTION.value:
                    self.offset += 1
                    function_length = decode_multibyte(self.scan_multibyte())
                    output += f"{self.offset:04}: {OpCode.PUSH_FUNCTION.name} [{function_length} bytes]\n"
                    self.offset += 1 + function_length
                case OpCode.GET_FUNCTION_ARG.value:
                    self.offset += 1
                    arg_address: int = decode_multibyte(self.scan_multibyte())
                    output += f"{self.offset:04}: {OpCode.GET_FUNCTION_ARG.name} @ {arg_address}\n"
                    self.offset += 1
                case OpCode.ADD.value:
                    output += f"{self.offset:04}: {OpCode.ADD.name}\n"
                    self.offset += 1
                case OpCode.SUBTRACT.value:
                    output += f"{self.offset:04}: {OpCode.SUBTRACT.name}\n"
                    self.offset += 1
                case OpCode.TIMES.value:
                    output += f"{self.offset:04}: {OpCode.TIMES.name}\n"
                    self.offset += 1
                case OpCode.DIVIDE.value:
                    output += f"{self.offset:04}: {OpCode.DIVIDE.name}\n"
                    self.offset += 1
                case OpCode.INT_DIVIDE.value:
                    output += f"{self.offset:04}: {OpCode.INT_DIVIDE.name}\n"
                    self.offset += 1
                case OpCode.MODULO.value:
                    output += f"{self.offset:04}: {OpCode.MODULO.name}\n"
                    self.offset += 1
                case OpCode.NEGATE.value:
                    output += f"{self.offset:04}: {OpCode.NEGATE.name}\n"
                    self.offset += 1
                case OpCode.EQUALS.value:
                    output += f"{self.offset:04}: {OpCode.EQUALS.name}\n"
                    self.offset += 1
                case OpCode.IS_EXACTLY.value:
                    output += f"{self.offset:04}: {OpCode.IS_EXACTLY.name}\n"
                    self.offset += 1
                case OpCode.LESS_THAN.value:
                    output += f"{self.offset:04}: {OpCode.LESS_THAN.name}\n"
                    self.offset += 1
                case OpCode.GREATER_THAN.value:
                    output += f"{self.offset:04}: {OpCode.GREATER_THAN.name}\n"
                    self.offset += 1
                case OpCode.LESS_THAN_EQUALS.value:
                    output += f"{self.offset:04}: {OpCode.LESS_THAN_EQUALS.name}\n"
                    self.offset += 1
                case OpCode.GREATER_THAN_EQUALS.value:
                    output += f"{self.offset:04}: {OpCode.GREATER_THAN_EQUALS.name}\n"
                    self.offset += 1
                case OpCode.NOT_EQUALS.value:
                    output += f"{self.offset:04}: {OpCode.NOT_EQUALS.name}\n"
                    self.offset += 1
                case OpCode.IS_EXACTLY_NOT.value:
                    output += f"{self.offset:04}: {OpCode.IS_EXACTLY_NOT.name}\n"
                    self.offset += 1
                case OpCode.ABS_VALUE.value:
                    output += f"{self.offset:04}: {OpCode.ABS_VALUE.name}\n"
                    self.offset += 1
                case OpCode.AND.value:
                    output += f"{self.offset:04}: {OpCode.AND.name}\n"
                    self.offset += 1
                case OpCode.OR.value:
                    output += f"{self.offset:04}: {OpCode.OR.name}\n"
                    self.offset += 1
                case OpCode.NOT.value:
                    output += f"{self.offset:04}: {OpCode.NOT.name}\n"
                    self.offset += 1
                case OpCode.LENGTH.value:
                    output += f"{self.offset:04}: {OpCode.LENGTH.name}\n"
                    self.offset += 1
                case OpCode.APPEND.value:
                    output += f"{self.offset:04}: {OpCode.APPEND.name}\n"
                    self.offset += 1
                case OpCode.PREPEND.value:
                    output += f"{self.offset:04}: {OpCode.PREPEND.name}\n"
                    self.offset += 1
                case OpCode.CONCAT.value:
                    output += f"{self.offset:04}: {OpCode.CONCAT.name}\n"
                    self.offset += 1
                case OpCode.TRANSPOSE.value:
                    output += f"{self.offset:04}: {OpCode.TRANSPOSE.name}\n"
                    self.offset += 1
                case OpCode.AS_TYPE.value:
                    output += f"{self.offset:04}: {OpCode.AS_TYPE.name}\n"
                    self.offset += 1
                case OpCode.ASSERT.value:
                    output += f"{self.offset:04}: {OpCode.ASSERT.name}\n"
                    self.offset += 1
                case OpCode.TYPE_OF.value:
                    output += f"{self.offset:04}: {OpCode.TYPE_OF.name}\n"
                    self.offset += 1
                case OpCode.ZERO_RANGE.value:
                    output += f"{self.offset:04}: {OpCode.ZERO_RANGE.name}\n"
                    self.offset += 1
                case OpCode.ONE_RANGE.value:
                    output += f"{self.offset:04}: {OpCode.ONE_RANGE.name}\n"
                    self.offset += 1
                case OpCode.FIRST.value:
                    output += f"{self.offset:04}: {OpCode.FIRST.name}\n"
                    self.offset += 1
                case OpCode.LAST.value:
                    output += f"{self.offset:04}: {OpCode.LAST.name}\n"
                    self.offset += 1
                case OpCode.INDEX.value:
                    output += f"{self.offset:04}: {OpCode.INDEX.name}\n"
                    self.offset += 1
                case _:
                    output += f"{self.offset:04}: UNKNOWN INSTRUCTION {instruction}\n"
                    self.offset += 1
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

    def write_push_string(self, value: str) -> None:
        # Encode the string as UTF-8 bytes
        string_bytes = value.encode("utf-8")
        # Write the length of the string as a multibyte integer
        self.write_byte(OpCode.PUSH_STRING)
        self.code.extend(encode_multibyte(len(string_bytes)))
        # Write the string bytes
        self.code.extend([int(byte) for byte in string_bytes])
        # Write the PUSH_STRING opcode
