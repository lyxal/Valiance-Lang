from common import MultibyteUtils
from common.Op import Op
from vm.CallStack import CallFrame
from vm.StackObject import S_String, StackObject, S_Number


class Interpreter:
    """
    All methods assume the ip starts in the intended position.

    E.g. If PUSH_NUMBER wants to read a multi-byte number, it
    is expected the call to getNextMultibyteNumber would begin with
    ip set to the byte after PUSH_NUMBER.
    """

    def __init__(self):
        self.program: list[int] = []
        self.ip: int = 0
        self.programLength: int = 0

    def moveIP(self, distance: int = 1):
        self.ip += distance

    def push(self, value: StackObject):
        """
        Push a value to the closest call frame
        """

        self.callStack[-1].push(value)

    def run(self, program: list[int]):
        self.program = program
        self.ip = 0
        self.programLength = len(program)

        self.callStack: list[CallFrame] = [CallFrame()]

        while self.ip < self.programLength:
            instruction: int = self.program[self.ip]
            match instruction:
                case Op.PUSH_NUMBER.value:
                    # PUSH_NUMBER <multibyte number>
                    self.moveIP()
                    number: int = self.getNextMultibyteNumber()
                    self.push(S_Number(number))
                case Op.PUSH_BYTE.value:
                    # PUSH_BYTE <byte>
                    self.moveIP()
                    self.push(S_Number(self.program[self.ip]))
                    self.moveIP()
                case Op.PUSH_DOUBLE_BYTE.value:
                    # PUSH_DOUBLE_BYTE <byte1> <byte2>
                    self.moveIP()
                    self.push(
                        S_Number(
                            MultibyteUtils.merge_bytes(
                                self.program[self.ip : self.ip + 2]
                            )
                        )
                    )
                    self.moveIP(2)  # To skip the two read bytes.
                case Op.PUSH_STRING.value:
                    # PUSH_STRING <string length> <string utf-8 bytes>
                    self.moveIP()
                    stringLength: int = self.getNextMultibyteNumber()
                    stringBytes: list[int] = self.program[
                        self.ip : self.ip + stringLength
                    ]
                    self.moveIP(stringLength)
                    string: str = bytes(stringBytes).decode("utf-8")
                    self.push(S_String(string))
                case Op.DUMP_STACK.value:
                    print(self.callStack[-1].stack)
                    self.moveIP()
                case _:
                    print("Unknown or unimplemented opcode")
                    self.moveIP()

    def getNextMultibyteNumber(self) -> int:
        """
        Collect bytes into a single multibyte number until
        the first byte with a leading bit of 0. The last
        byte will be included. The ip will be left after the
        multibyte number
        """
        collectedBytes: list[int] = []
        while self.ip > self.programLength and self.program[self.ip] & 128 == 128:
            collectedBytes.append(self.program[self.ip])
            self.moveIP()

        # This will leave the IP resting on the last byte of the multibyte
        # number. Therefore it needs to be added to the collection, and
        # the IP needs to be moved once more

        collectedBytes.append(self.program[self.ip])
        self.moveIP()

        # Decode the multibyte number

        return MultibyteUtils.decode_multibyte(collectedBytes)
