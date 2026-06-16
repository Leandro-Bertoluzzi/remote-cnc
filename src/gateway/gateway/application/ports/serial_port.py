"""SerialPort port — the minimal serial communication interface."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SerialPort(Protocol):
    """Structural interface for a serial communication adapter."""

    @classmethod
    def get_ports(cls) -> list:
        """Return a list of available serial ports."""
        ...

    def startConnection(self, port: str, baudrate: int, timeout: float = 2) -> str:
        """Open the serial port and return the first message received."""
        ...

    def stopConnection(self) -> None:
        """Close the serial port."""
        ...

    def sendLine(self, code: str) -> None:
        """Send a text line over the serial port."""
        ...

    def sendBytes(self, code: bytes) -> None:
        """Send raw bytes over the serial port."""
        ...

    def readLine(self) -> str:
        """Read one line from the serial port."""
        ...

    def readLineUntilMessage(self, max_retries: int = 30) -> str:
        """Read lines until a non-empty message is received."""
        ...

    def waiting(self) -> bool:
        """Return True if there is data waiting in the input buffer."""
        ...
