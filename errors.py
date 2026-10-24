"""Expected errors reported to the user without a traceback."""


class FlyInError(Exception):
    """Represent an input, routing, or simulation error."""


class ParseError(FlyInError):
    """Report a map syntax error with its source line."""

    def __init__(self, line: int, reason: str) -> None:
        """Build a diagnostic identifying the failing line."""
        super().__init__(f"line {line}: {reason}")


class SimulationError(FlyInError):
    """Report an invalid movement or an incomplete delivery."""
