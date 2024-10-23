from abc import ABC, abstractmethod
from ..types import GrblResponse
from typing import Optional


class GrblParserGeneric(ABC):
    """Base class to define GRBL message parsers
    """
    @staticmethod
    @abstractmethod
    def parse(line: str) -> Optional[GrblResponse]:
        """Parses a message from GRBL.

        Args:
            line: A string representing a GRBL message.

        Returns:
            A tuple containing the message type and payload,
            or None if the line is not a valid GRBL message.
        """
        raise NotImplementedError   # pragma: no cover
