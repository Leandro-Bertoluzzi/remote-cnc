"""Fake implementations of gateway ports for use in tests."""

from __future__ import annotations


class FakeSerial:
    """In-memory implementation of ``SerialPort`` for use in unit tests.

    Usage::

        fake = FakeSerial()
        fake.start_return = "Grbl 1.1h"        # what startConnection returns
        fake.start_side_effect = SerialException("boom")  # or raise on start

        fake.readLine returns queued lines (FIFO) from ``fake.lines``.

    Attributes
    ----------
    lines:
        Queue of strings to return from ``readLine`` / ``readLineUntilMessage``.
    sent_lines:
        List of strings passed to ``sendLine``.
    sent_bytes:
        List of byte sequences passed to ``sendBytes``.
    start_call_count:
        Number of times ``startConnection`` was called.
    stop_call_count:
        Number of times ``stopConnection`` was called.
    """

    def __init__(self):
        self.start_return: str = ""
        self.start_side_effect: Exception | None = None
        self.read_line_side_effect: Exception | None = None
        self.lines: list[str] = []
        self.sent_lines: list[str] = []
        self.sent_bytes: list[bytes] = []
        self.start_call_count: int = 0
        self.stop_call_count: int = 0

    @classmethod
    def get_ports(cls) -> list:
        return []

    def startConnection(self, port: str, baudrate: int, timeout: float = 2) -> str:
        self.start_call_count += 1
        if self.start_side_effect is not None:
            raise self.start_side_effect
        return self.start_return

    def stopConnection(self) -> None:
        self.stop_call_count += 1

    def sendLine(self, code: str) -> None:
        self.sent_lines.append(code)

    def sendBytes(self, code: bytes) -> None:
        self.sent_bytes.append(code)

    def readLine(self) -> str:
        if self.read_line_side_effect is not None:
            raise self.read_line_side_effect
        return self.lines.pop(0) if self.lines else ""

    def readLineUntilMessage(self, max_retries: int = 30) -> str:
        return self.lines.pop(0) if self.lines else ""

    def waiting(self) -> bool:
        return bool(self.lines)
