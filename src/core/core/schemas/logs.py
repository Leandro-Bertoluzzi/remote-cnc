from pydantic import BaseModel


class LogsResponse(BaseModel):
    file_name: str
    description: str
