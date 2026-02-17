from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    language = Column(String(10), default="en", nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
