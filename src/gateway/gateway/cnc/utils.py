"""GRBL-specific utilities."""

from __future__ import annotations

import re

from gateway.cnc.constants import GRBL_SETTINGS

# ---------------------------------------------------------------------------
# Jog unit / distance-mode string values
# (kept as plain strings for backward compatibility with existing callers;
#  core.domain.cnc.JogUnit / JogDistanceMode carry the same values)
# ---------------------------------------------------------------------------

JOG_UNIT_MILIMETERS = "milimeters"
JOG_UNIT_INCHES = "inches"
JOG_DISTANCE_ABSOLUTE = "distance_absolute"
JOG_DISTANCE_INCREMENTAL = "distance_incremental"

# Regular expressions
grbl_setting_pattern = re.compile(r"^\$(\d+)=(\d+\.?\d*)$")


def build_jog_command(
    x: float,
    y: float,
    z: float,
    feedrate: float,
    *,
    units: str | None = None,
    distance_mode: str | None = None,
    machine_coordinates: bool = False,
) -> str:
    """Build a GRBL ``$J=`` jog command string from the given parameters."""
    parts = ["$J="]

    if machine_coordinates:
        parts.append("G53")

    if distance_mode == JOG_DISTANCE_ABSOLUTE:
        parts.append("G90")
    elif distance_mode == JOG_DISTANCE_INCREMENTAL:
        parts.append("G91")

    if units == JOG_UNIT_INCHES:
        parts.append("G20")
    elif units == JOG_UNIT_MILIMETERS:
        parts.append("G21")

    if x or distance_mode == JOG_DISTANCE_ABSOLUTE:
        parts.append(f"X{x}")
    if y or distance_mode == JOG_DISTANCE_ABSOLUTE:
        parts.append(f"Y{y}")
    if z or distance_mode == JOG_DISTANCE_ABSOLUTE:
        parts.append(f"Z{z}")
    if feedrate:
        parts.append(f"F{feedrate}")

    return " ".join(parts).replace("$J= ", "$J=")


def is_setting_update_command(command: str) -> bool:
    """Return ``True`` if *command* is a GRBL setting update (e.g. ``$23=5``)."""
    m = grbl_setting_pattern.search(command)
    if not m:
        return False
    return int(m.group(1)) <= 132


def get_grbl_setting(key: str):
    """Return the metadata dict for GRBL setting *key*, or ``None``."""
    for element in GRBL_SETTINGS:
        if element["setting"] == key:
            return element
    return None
