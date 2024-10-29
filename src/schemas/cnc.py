from pydantic import BaseModel
from typing import Literal


class CncCommand(BaseModel):
    command: str


class CncJogCommand(BaseModel):
    x: float
    y: float
    z: float
    feedrate: float
    units: Literal["milimeters", "inches"]
    mode: Literal["distance_absolute", "distance_incremental"]


class CncJogResponse(BaseModel):
    command: str
