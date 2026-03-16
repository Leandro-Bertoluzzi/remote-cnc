import datetime

from pydantic import BaseModel, ConfigDict


class ToolRequest(BaseModel):
    name: str
    description: str


class ToolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    added_at: datetime.datetime
