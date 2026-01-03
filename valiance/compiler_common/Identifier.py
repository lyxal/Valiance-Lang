class Identifier:
    def __init__(
        self, name: str = "", property: Identifier | None = None, is_error: bool = False
    ):
        self.name: str = name
        self.property: Identifier | None = property
        self.error: bool = is_error

    def __repr__(self):
        if self.property is not None:
            return f"{self.name}.{self.property}"
        return self.name

    def __str__(self):
        return self.__repr__()
