import datetime
from pydantic import BaseModel


class MaterialRequestModel(BaseModel):
    name: str
    description: str


class MaterialResponseModel(BaseModel):
    id: int
    name: str
    description: str
    added_at: datetime.datetime
