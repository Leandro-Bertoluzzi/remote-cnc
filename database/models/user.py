import bcrypt
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from database.base import Base

VALID_ROLES = ['user', 'admin']

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    role = Column(String)

    # Virtual columns
    tasks = relationship('Task', backref='user', foreign_keys='Task.user_id')
    files = relationship('File', backref='user')

    def __init__(self, name, email, password, role):
        self.name = name
        self.email = email
        self.role = role
        # Hashing the password
        self.password = self.encryptPassword(password)

    def encryptPassword(self, password: str):
        """Generates a hash for the password"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def validatePassword(self, testPassword: str):
        """Compares a given password with the actual one"""
        return bcrypt.checkpw(testPassword.encode('utf-8'), self.password)

    def __repr__(self):
        return f"<User: {self.name}, email: {self.email}, role: {self.role}>"
