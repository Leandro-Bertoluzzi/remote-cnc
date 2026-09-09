from pydantic import BaseModel


class GenericResponse(BaseModel):
    success: str
