from compiler_common.Identifier import Identifier


class Tag:
    def __init__(self):
        pass


class DataTag(Tag):
    def __init__(self, name: Identifier, depth: int):
        self.name = name
        self.depth = depth


class ElementTag(Tag):
    def __init__(self, name: Identifier):
        self.name = name
        self.depth = -1
