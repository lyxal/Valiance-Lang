from bytecode.ops import OpCode
from bytecode.stackobject import StackList, StackNumber, StackObject, StackString
from bytecode.utils import decode_multibyte, merge_bytes


class Interpreter:
    def __init__(self, bytecode: list[int]):
        self.bytecode = bytecode
        self.stack: list[StackObject] = []
        self.ip = 0

    def run(self):
        while self.ip < len(self.bytecode):
            op = self.bytecode[self.ip]
            self.ip += 1

            match op:
                case OpCode.POP.value:
                    if not self.stack:
                        raise IndexError("Stack underflow")
                    self.stack.pop()
                case OpCode.DUP.value:
                    if not self.stack:
                        raise IndexError("Stack underflow")
                    self.stack.append(self.stack[-1])
                case OpCode.SWAP.value:
                    if len(self.stack) < 2:
                        raise IndexError("Stack underflow")
                    a = self.stack.pop()
                    b = self.stack.pop()
                    self.stack.append(a)
                    self.stack.append(b)
                case OpCode.JMP.value:
                    value = self.scan_multibyte()
                    self.ip += decode_multibyte(value)
                case OpCode.JMP_B1.value:
                    value = self.bytecode[self.ip]
                    self.ip += 1
                    self.ip += value
                case OpCode.PRINT.value:
                    value = self.stack.pop()
                    print("STDOUT: ", value.value)
                case OpCode.JNZ.value:
                    if not self.stack:
                        raise IndexError("Stack underflow")
                    value = self.stack.pop()
                    jump_value = self.scan_multibyte()
                    if not isinstance(value, StackNumber):
                        raise TypeError("Condition must be a number")
                    if value.value != 0:
                        self.ip += decode_multibyte(jump_value)
                case OpCode.JZ.value:
                    if not self.stack:
                        raise IndexError("Stack underflow")
                    value = self.stack.pop()
                    jump_value = self.scan_multibyte()
                    if not isinstance(value, StackNumber):
                        raise TypeError("Condition must be a number")
                    if value.value == 0:
                        self.ip += decode_multibyte(jump_value)
                case OpCode.PUSH_INT.value:
                    value = self.scan_multibyte()
                    self.stack.append(StackNumber(decode_multibyte(value)))
                case OpCode.PUSH_INT_BYTE.value:
                    value = self.bytecode[self.ip]
                    self.ip += 1
                    self.stack.append(StackNumber(value))
                case OpCode.PUSH_INT_BYTE_2.value:
                    value = self.bytecode[self.ip : self.ip + 2]
                    self.ip += 2
                    merged_value = merge_bytes(value)
                    self.stack.append(StackNumber(merged_value))
                case OpCode.DUMP_STACK.value:
                    print("Stack dump:")
                    for i, item in enumerate(self.stack):
                        print(f"  {i}: {item}")
                case OpCode.PUSH_STRING.value:
                    length = decode_multibyte(self.scan_multibyte())
                    string_value = bytearray(
                        self.bytecode[self.ip : self.ip + length]
                    ).decode("utf-8")
                    self.ip += length
                    self.stack.append(StackString(string_value))
                case OpCode.PUSH_LIST.value:
                    length = decode_multibyte(self.scan_multibyte())
                    list_value = [self.stack.pop() for _ in range(length)]
                    self.stack.append(StackList(list_value))
                case OpCode.ADD.value:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    if not isinstance(a, StackNumber) or not isinstance(b, StackNumber):
                        raise TypeError("Operands must be numbers")
                    result = a.value + b.value
                    self.stack.append(StackNumber(result))
                case _:
                    raise ValueError(f"Unknown opcode: {op}")
        return self.stack

    def scan_multibyte(self) -> list[int]:
        bits: list[int] = []
        while self.bytecode[self.ip] & 128:
            bits.append(self.bytecode[self.ip])
            self.ip += 1
        bits.append(self.bytecode[self.ip])
        self.ip += 1
        return bits
