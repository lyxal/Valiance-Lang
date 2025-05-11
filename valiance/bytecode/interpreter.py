from bytecode.ops import OpCode
from bytecode.stackobject import StackNumber, StackObject
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
                case OpCode.PRINT.value:
                    value = self.stack.pop()
                    print(value.value)
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
