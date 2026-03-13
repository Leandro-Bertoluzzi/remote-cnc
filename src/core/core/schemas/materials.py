import datetime
from pydantic import BaseModel


class MaterialRequest(BaseModel):
    name: str
    description: str


class MaterialResponse(BaseModel):
    id: int
    name: str
    description: str
    added_at: datetime.datetime

    class Config:
        orm_mode = True
