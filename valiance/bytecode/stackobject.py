class StackObject:
    def __init__(self):
        self.value = None


class StackNumber(StackObject):
    def __init__(self, value: int):
        self.value = value

    def __repr__(self):
        return f"StackNumber({self.value})"
