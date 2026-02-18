"""Schemas for import functionality."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_serializer
from decimal import Decimal


class ImportTransaction(BaseModel):
    """Single transaction from import."""
    raw_description: str
    amount: float
    transaction_date: Optional[datetime] = None
    mcc_code: Optional[str] = None
    type: str  # 'income' or 'expense'
    suggested_category: Optional[str] = None
    confidence: str = "low"  # 'high', 'medium', 'low'
    confidence_score: float = 0.0
    # Duplicate detection
    is_duplicate: bool = False
    duplicate_count: int = 0
    
    @field_serializer('amount')
    def serialize_amount(self, amount: float) -> float:
        return round(amount, 2)
    
    @field_serializer('mcc_code')
    def serialize_mcc(self, mcc: Optional[str]) -> Optional[str]:
        if mcc:
            # Clean up MCC - remove .0 suffix if present, limit to 4 chars
            clean = mcc.replace('.0', '')[:4]
            return clean if clean else None
        return None


class ImportPreviewRequest(BaseModel):
    """Request to preview import."""
    bank_type: Optional[str] = None  # 'tinkoff', 'sber', 'alfa', etc.


class ImportPreviewResponse(BaseModel):
    """Response with parsed transactions for review."""
    transactions: List[ImportTransaction]
    total_count: int
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    duplicate_count: int = 0
    detected_bank: Optional[str] = None


class ImportConfirmRequest(BaseModel):
    """Request to confirm import."""
    transactions: List[ImportTransaction]
    save_patterns: bool = True  # Learn from user's choices


class ImportConfirmResponse(BaseModel):
    """Response after import confirmation."""
    imported_count: int
    saved_patterns: int


class CategorySuggestionRequest(BaseModel):
    """Request to get category suggestion for a raw description."""
    raw_description: str
    mcc_code: Optional[str] = None


class CategorySuggestionResponse(BaseModel):
    """Response with category suggestion."""
    category: str
    confidence: str
    score: float
