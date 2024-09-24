from pydantic import BaseModel


class GenericResponse(BaseModel):
    success: str


class PubSubMessage(BaseModel):
    message: str
