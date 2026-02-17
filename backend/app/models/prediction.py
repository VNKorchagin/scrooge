from datetime import datetime
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    predicted_date = Column(DateTime, nullable=False)
    predicted_amount = Column(Numeric(12, 2), nullable=False)
    confidence = Column(Numeric(5, 4), nullable=True)  # 0.0000 - 1.0000
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="predictions")
