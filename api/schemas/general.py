from pydantic import BaseModel


class GenericResponseModel(BaseModel):
    success: str
