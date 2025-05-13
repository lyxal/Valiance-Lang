from vm.TypeTag import TypeTag


class StackObject:
    def __init__(self):
        self.value = None

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return repr(self.value)


class S_Number(StackObject):
    def __init__(self, value: int):
        self.value: int = value


class S_String(StackObject):
    def __init__(self, value: str):
        self.value: str = value


class S_List(StackObject):
    def __init__(self, value: list[StackObject], baseType: TypeTag):
        self.value: list[StackObject] = value
        self.baseType = baseType
