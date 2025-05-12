class StackObject:
    def __init__(self):
        self.value = None


class StackNumber(StackObject):
    def __init__(self, value: int):
        self.value = value

    def __repr__(self):
        return f"StackNumber({self.value})"


class StackString(StackObject):
    def __init__(self, value: str):
        self.value = value

    def __repr__(self):
        return f"StackString({self.value})"


class StackList(StackObject):
    def __init__(self, value: list[StackObject]):
        self.value = value

    def __repr__(self):
        return f"StackList({self.value})"


class StackFunction(StackObject):
    def __init__(self, value: list[int]):
        self.value = value  # The bytecode of the function

    def __repr__(self):
        return f"StackFunction({self.value})"
