from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    language = Column(String(10), default="en", nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    vault_accounts = relationship("VaultAccount", back_populates="user", cascade="all, delete-orphan")
    vault_snapshots = relationship("VaultSnapshot", back_populates="user", cascade="all, delete-orphan")
    vault_projection_settings = relationship("VaultProjectionSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transaction_patterns = relationship("TransactionPattern", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None or not self.is_active
