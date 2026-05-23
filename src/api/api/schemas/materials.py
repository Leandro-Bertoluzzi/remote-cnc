import datetime

from pydantic import BaseModel, ConfigDict


class MaterialRequest(BaseModel):
    name: str
    description: str


class MaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    added_at: datetime.datetime
