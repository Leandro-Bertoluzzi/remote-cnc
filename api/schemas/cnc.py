from pydantic import BaseModel
from typing import Literal


class CncCommandModel(BaseModel):
    command: str


class CncJogCommandModel(BaseModel):
    x: float
    y: float
    z: float
    feedrate: float
    units: Literal["milimeters", "inches"]
    mode: Literal["distance_absolute", "distance_incremental"]


class CncJogResponseModel(BaseModel):
    command: str
