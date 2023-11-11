from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..base import Base

class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    file_name = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime)

    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'))

    # Virtual columns
    tasks = relationship('Task', backref='file')

    def __init__(self, user_id, file_name, file_path, created_at=datetime.now()):
        self.user_id = user_id
        self.file_name = file_name
        self.file_path = file_path
        self.created_at = created_at

    def __repr__(self):
        return f"<File: {self.file_name}, path: {self.file_path}, user ID: {self.user_id}, created at: {self.created_at}>"
