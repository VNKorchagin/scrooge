"""Model for storing user transaction patterns for auto-categorization."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class TransactionPattern(Base):
    """Stores patterns for auto-categorizing imported transactions.
    
    When user confirms a category for a raw description like "PYATYOROCHKA",
    we store this mapping to auto-suggest next time.
    """
    __tablename__ = "transaction_patterns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Raw description from bank statement (e.g., "PYATYOROCHKA 6431 MOSCOW")
    raw_description = Column(String, nullable=False)
    
    # Normalized pattern for matching (e.g., "pyatyorochka")
    normalized_pattern = Column(String, nullable=False, index=True)
    
    # Assigned category
    category_name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    
    # Transaction type
    type = Column(String, nullable=False)  # 'income' or 'expense'
    
    # Optional: MCC code if available
    mcc_code = Column(String(4), nullable=True)
    
    # Confidence score based on user confirmations
    usage_count = Column(Integer, default=1, nullable=False)
    
    # When this pattern was created/last used
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="transaction_patterns")
    category = relationship("Category")

    __table_args__ = (
        # Index for fast lookup by normalized pattern
        Index('ix_patterns_user_normalized', 'user_id', 'normalized_pattern'),
    )
