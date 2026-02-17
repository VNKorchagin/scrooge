from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal

from app.models.transaction import TransactionType


class TransactionBase(BaseModel):
    type: TransactionType
    amount: Decimal = Field(..., max_digits=12, decimal_places=2)
    category_name: str
    transaction_date: datetime
    description: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


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
