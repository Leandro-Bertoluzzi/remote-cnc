from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import MappedAsDataclass

try:
    from ..config import SQLALCHEMY_DATABASE_URI
except ImportError:
    from config import SQLALCHEMY_DATABASE_URI

engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)


class Base(MappedAsDataclass, DeclarativeBase):
    """subclasses will be converted to dataclasses"""
    pass
