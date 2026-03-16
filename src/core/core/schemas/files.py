import datetime

from pydantic import BaseModel, ConfigDict, Field


class FileUpdate(BaseModel):
    file_name: str


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str = Field(alias="file_name")
    created_at: datetime.datetime
    user_id: int


class FileContentResponse(BaseModel):
    content: str
