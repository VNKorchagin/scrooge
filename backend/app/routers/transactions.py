from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.transaction import Transaction, TransactionCreate, TransactionFilter, TransactionUpdate
from app.models.transaction import TransactionType
from app.services.transaction_service import TransactionService

router = APIRouter()


def normalize_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert offset-aware datetime to offset-naive (UTC) for DB compatibility."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # Convert to UTC and remove timezone info
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class TransactionListResponse:
    """Response model for transaction list."""
    def __init__(self, items: List[Transaction], total: int, limit: int, offset: int):
        self.items = items
        self.total = total
        self.limit = limit
        self.offset = offset


@router.get("", response_model=dict)
async def list_transactions(
    type: Optional[TransactionType] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    category_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get transactions with filters and pagination"""
    # Normalize datetime filters to offset-naive UTC for DB compatibility
    filters = TransactionFilter(
        type=type,
        date_from=normalize_datetime(date_from),
        date_to=normalize_datetime(date_to),
        category_id=category_id,
        limit=limit,
        offset=offset
    )
    
    transactions, total = await TransactionService.get_list(db, current_user_id, filters)
    
    # Convert SQLAlchemy models to Pydantic schemas
    transaction_schemas = [Transaction.model_validate(t) for t in transactions]
    
    return {
        "items": transaction_schemas,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.post("", response_model=Transaction)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new transaction.
    If category doesn't exist, it will be created automatically.
    """
    return await TransactionService.create(db, transaction_data, current_user_id)


@router.patch("/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: int,
    updates: TransactionUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update a transaction (only if owned by current user)."""
    transaction = await TransactionService.get_by_id(db, transaction_id, current_user_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Convert to dict, excluding None values
    update_data = updates.model_dump(exclude_unset=True, exclude_none=True)
    
    updated_transaction = await TransactionService.update(db, transaction, update_data)
    return Transaction.model_validate(updated_transaction)


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a transaction (only if owned by current user)"""
    deleted = await TransactionService.delete(db, transaction_id, current_user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return {"message": "Transaction deleted successfully"}
