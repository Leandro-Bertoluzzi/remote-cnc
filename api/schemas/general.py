from pydantic import BaseModel


class GenericResponseModel(BaseModel):
    success: str


class PubSubMessageModel(BaseModel):
    message: str
