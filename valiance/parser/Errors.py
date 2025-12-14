from valiance.parser.AST import Location


class GenericParseError:
    """Represents a generic parsing error"""

    def __init__(self, message: str, location: Location):
        self.message = message
        self.location = location

    def __str__(self):
        return f"ParseError at (line {self.location.line}, column {self.location.column}): {self.message}"
