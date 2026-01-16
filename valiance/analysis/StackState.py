# Abstract stack state
from abc import abstractmethod

from valiance.vtypes.VTypes import VType

type typelist = list[VType]


class StackState:
    @abstractmethod
    def push(self, ty: VType): ...
    @abstractmethod
    def pop(self): ...
    @abstractmethod
    def pop_types(self, types: list[VType]): ...
    @abstractmethod
    def pop_n(self, n: int): ...


class SingleStack(StackState):
    def __init__(self, inputs: typelist | None = None):
        self.stack: typelist = inputs[::] if inputs is not None else []
        self.inputs = inputs
        self.input_index = 0

    def _get_next_input(self) -> VType:
        assert self.inputs is not None
        ty = self.inputs[self.input_index]
        self.input_index += 1
        self.input_index %= len(self.inputs)
        return ty

    def push(self, ty: VType):
        self.stack.append(ty)

    def pop(self):
        self.stack.pop()

    def pop_types(self, types: list[VType]):
        # Glorified pop n. pop_types is majorly useful when doing
        # multiversal overload inference
        for _ in reversed(types):
            self.stack.pop()

    def pop_n(self, n: int):
        self.stack = self.stack[-n:]

    def pad_to_length(self, length: int):
        if not self.inputs:
            return
        while len(self.stack) < length:
            self.stack.append(self._get_next_input())


class Universe:
    def __init__(self):
        self.stack: typelist = []
        self.inputs: typelist = []


class MultiStack(StackState):
    def __init__(self):
        self.universes: list[Universe] = []

    def push(self, ty: VType):
        for universe in self.universes:
            universe.stack.append(ty)

    def pop(self):
        for universe in self.universes:
            universe.stack.pop()

    def pop_types(self, types: list[VType]):
        for universe in self.universes:
            if len(universe.stack) < len(types):
                # Where a universe stack wouldn't have enough types,
                # the types become inputs instead
                needed = len(types) - len(universe.stack)
                universe.inputs.extend(reversed(types[-needed:]))
                universe.stack = []
            else:
                for _ in reversed(types):
                    universe.stack.pop()

    def pop_n(self, n: int):
        for universe in self.universes:
            universe.stack = universe.stack[-n:]
