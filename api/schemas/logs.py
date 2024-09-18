from pydantic import BaseModel


class LogsResponseModel(BaseModel):
    file_name: str
    description: str
