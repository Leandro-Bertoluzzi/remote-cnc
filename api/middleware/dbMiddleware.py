from core.database.base import Session as SessionLocal
from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Annotated


def get_db():
    database = SessionLocal()
    database.expire_on_commit = False
    try:
        yield database
    finally:
        database.close()


# Type definitions
GetDbSession = Annotated[Session, Depends(get_db)]
