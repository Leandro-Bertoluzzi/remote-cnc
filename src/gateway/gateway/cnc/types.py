"""GRBL-specific type definitions."""

from __future__ import annotations

from typing import Optional

from core.domain.cnc import Coordinates, DeviceSetting, DeviceSettings, ParserState, Status
from typing_extensions import TypedDict

ModalGroup = TypedDict("ModalGroup", {"group": str, "modes": list[str]})
GrblError = TypedDict("GrblError", {"code": int, "message": str, "description": str})

# Aliases
GrblSetting = DeviceSetting
GrblSettings = DeviceSettings

ProbeStatus = TypedDict("ProbeStatus", {"x": float, "y": float, "z": float, "result": bool})
GrblControllerParameters = TypedDict(
    "GrblControllerParameters",
    {
        "G54": Coordinates,
        "G55": Coordinates,
        "G56": Coordinates,
        "G57": Coordinates,
        "G58": Coordinates,
        "G59": Coordinates,
        "G28": Coordinates,
        "G30": Coordinates,
        "G92": Coordinates,
        "TLO": float,
        "PRB": ProbeStatus,
    },
)
GrblBuildInfo = TypedDict(
    "GrblBuildInfo",
    {
        "version": str,
        "comment": str,
        "optionCode": str,
        "blockBufferSize": int,
        "rxBufferSize": int,
    },
)

GrblControllerState = TypedDict(
    "GrblControllerState", {"status": Status, "parserstate": ParserState}
)
GrblResponse = tuple[Optional[str], dict[str, str]]
