class Location:
    """Represents a location in the source code"""

    def __init__(self, line: int, column: int):
        self.line = line
        self.column = column
