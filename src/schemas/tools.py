import datetime
from pydantic import BaseModel


class ToolRequest(BaseModel):
    name: str
    description: str


class ToolResponse(BaseModel):
    id: int
    name: str
    description: str
    added_at: datetime.datetime

    class Config:
        orm_mode = True
