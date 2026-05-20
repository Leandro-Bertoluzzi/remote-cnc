"""Firmware-agnostic CNC domain types.

These types define the data contract shared across all modules.
They must not reference any specific firmware.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from typing_extensions import TypedDict

# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

Coordinates = dict[str, float]
PositionType = Literal["mpos", "wpos"]

# ---------------------------------------------------------------------------
# Status / parser-state
# ---------------------------------------------------------------------------

Status = TypedDict(
    "Status",
    {
        "activeState": str,
        "subState": Optional[int],
        "mpos": Coordinates,
        "wpos": Coordinates,
        "ov": list[int],
        "wco": Coordinates,
        "pinstate": Optional[str],
        "buffer": Optional[dict[str, int]],
        "line": Optional[int],
        "accessoryState": Optional[str],
    },
)

ParserState = TypedDict(
    "ParserState",
    {"modal": dict[str, str], "tool": int, "feedrate": float, "spindle": float},
)

# ---------------------------------------------------------------------------
# Jog parameters
# ---------------------------------------------------------------------------


class JogUnit(str, Enum):
    """Unit system for jog movements."""

    MILIMETERS = "milimeters"
    INCHES = "inches"


class JogDistanceMode(str, Enum):
    """Distance mode for jog movements."""

    ABSOLUTE = "distance_absolute"
    INCREMENTAL = "distance_incremental"


# ---------------------------------------------------------------------------
# Device settings
# ---------------------------------------------------------------------------

DeviceSetting = TypedDict(
    "DeviceSetting",
    {"value": str, "message": str, "units": str, "description": str},
)

DeviceSettings = dict[str, DeviceSetting]
