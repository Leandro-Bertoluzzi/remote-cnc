from sqlalchemy import Column, String, Integer, Date
from database.base import Base

VALID_ROLES = ['user', 'admin']

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    role = Column(String)

    def __init__(self, name, email, password, role):
        self.name = name
        self.email = email
        self.password = password
        self.role = role

    def __repr__(self):
        return f"<User: {self.name}, email: {self.email}, role: {self.role}>"
