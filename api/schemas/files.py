import datetime
from pydantic import BaseModel, Field


class FileUpdateModel(BaseModel):
    file_name: str


class FileResponseModel(BaseModel):
    id: int
    name: str = Field(alias="file_name")
    created_at: datetime.datetime
    user_id: int

    class Config:
        allow_population_by_field_name = True


class FileContentResponseModel(BaseModel):
    content: str
