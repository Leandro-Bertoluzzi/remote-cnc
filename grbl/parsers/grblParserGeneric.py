from abc import abstractmethod

class GrblParserGeneric:
    """Base class to define GRBL message parsers
    """
    @staticmethod
    @abstractmethod
    def parse(line: str) -> tuple[str, dict[str, str]] | None:
        """Parses a message from GRBL.

        Args:
            line: A string representing a GRBL message.

        Returns:
            A tuple containing the message type and payload, or None if the line is not a valid GRBL message.
        """
        pass
