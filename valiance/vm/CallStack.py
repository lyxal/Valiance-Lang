from vm.StackObject import StackObject


class CallFrame:
    def __init__(self):
        self.stack: list[StackObject] = []
        self.variables: dict[str, StackObject] = {}

    def push(self, value: StackObject):
        self.stack.append(value)

    def pop(self) -> StackObject:
        return self.stack.pop()
