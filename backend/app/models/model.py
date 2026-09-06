from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Model(Base):
    __tablename__ = "models"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")
