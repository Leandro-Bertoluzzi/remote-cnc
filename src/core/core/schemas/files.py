import datetime
from pydantic import BaseModel, Field


class FileUpdate(BaseModel):
    file_name: str


class FileResponse(BaseModel):
    id: int
    name: str = Field(alias="file_name")
    created_at: datetime.datetime
    user_id: int

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class FileContentResponse(BaseModel):
    content: str
