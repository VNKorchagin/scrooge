from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from decimal import Decimal

from app.models.transaction import TransactionType


class TransactionBase(BaseModel):
    type: TransactionType
    amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    category_name: str
    transaction_date: Optional[datetime] = None
    description: Optional[str] = None
    
    @field_validator('transaction_date')
    @classmethod
    def normalize_datetime(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Convert offset-aware datetime to offset-naive (UTC)."""
        if v is None:
            return v
        if v.tzinfo is not None:
            # Convert to UTC and remove timezone info
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction. All fields are optional."""
    transaction_date: Optional[datetime] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)
    category_name: Optional[str] = None
    
    @field_validator('transaction_date')
    @classmethod
    def normalize_datetime(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Convert offset-aware datetime to offset-naive (UTC)."""
        if v is None:
            return v
        if v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v


class Transaction(TransactionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    category_id: Optional[int] = None
    raw_description: Optional[str] = None
    source: str
    created_at: datetime


class TransactionFilter(BaseModel):
    type: Optional[TransactionType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    category_id: Optional[int] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)
