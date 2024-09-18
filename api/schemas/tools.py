import datetime
from pydantic import BaseModel


class ToolRequestModel(BaseModel):
    name: str
    description: str


class ToolResponseModel(BaseModel):
    id: int
    name: str
    description: str
    added_at: datetime.datetime
