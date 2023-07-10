from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from database.base import Base
from datetime import datetime

class Tool(Base):
    __tablename__ = 'tools'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    added_at = Column(DateTime)

    # Virtual columns
    tasks = relationship('Task', backref='tool')

    def __init__(self, name, description, added_at=datetime.now()):
        self.name = name
        self.description = description
        self.added_at = added_at

    def __repr__(self):
        return f"<Tool: {self.name}, description: {self.description}, added at: {self.added_at}>"

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "added_at": self.added_at
        }
