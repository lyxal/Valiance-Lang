from valiance.parser.AST import Location


class GenericParseError:
    """Represents a generic parsing error"""

    def __init__(self, message: str, location: Location):
        self.message = message
        self.location = location

    def __str__(self):
        return f"ParseError at (line {self.location.line}, column {self.location.column}): {self.message}"


class UnexpectedEndOfInputError(Exception):
    """Raised when the parser encounters an unexpected end of input."""

    pass


class ParserError(Exception):
    """Raised for general parser errors."""

    pass


class EndOfFileTokenError(ParserError):
    """Raised when an unexpected EOF token is encountered."""

    pass
