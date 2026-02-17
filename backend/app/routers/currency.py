from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.currency_service import CurrencyService
from app.services.user_service import UserService
from app.services.transaction_service import TransactionService
from app.schemas.user import CurrencyRate, UserUpdate
from app.schemas.transaction import TransactionFilter

router = APIRouter()


@router.get("/rate", response_model=CurrencyRate)
async def get_currency_rate(
    from_currency: str = "USD",
    to_currency: str = "RUB",
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get current exchange rate between currencies."""
    rate = await CurrencyService.get_exchange_rate(from_currency, to_currency)
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not fetch exchange rate"
        )
    
    from datetime import datetime
    return CurrencyRate(
        from_currency=from_currency,
        to_currency=to_currency,
        rate=rate,
        timestamp=datetime.utcnow()
    )


@router.post("/convert")
async def convert_currency(
    new_currency: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Convert all user transactions to new currency.
    Returns the exchange rate and preview of converted totals.
    """
    # Get current user
    user = await UserService.get_by_id(db, current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_currency = user.currency
    
    if current_currency == new_currency:
        raise HTTPException(
            status_code=400, 
            detail=f"Already using {new_currency}"
        )
    
    # Get exchange rate
    rate = await CurrencyService.get_exchange_rate(current_currency, new_currency)
    if not rate:
        raise HTTPException(
            status_code=503,
            detail=f"Could not get exchange rate for {current_currency} to {new_currency}"
        )
    
    # Get user's transactions for preview (max 100 for preview)
    filters = TransactionFilter(limit=100, offset=0)
    transactions, total = await TransactionService.get_list(db, current_user_id, filters)
    
    # Calculate totals in current currency
    from decimal import Decimal
    current_income = sum(tx.amount for tx in transactions if tx.type.value == "income")
    current_expense = sum(tx.amount for tx in transactions if tx.type.value == "expense")
    
    # Calculate totals in new currency
    new_income = CurrencyService.convert_amount(current_income, current_currency, new_currency, rate)
    new_expense = CurrencyService.convert_amount(current_expense, current_currency, new_currency, rate)
    
    return {
        "current_currency": current_currency,
        "new_currency": new_currency,
        "rate": rate,
        "preview": {
            "current_income": float(current_income),
            "current_expense": float(current_expense),
            "new_income": float(new_income),
            "new_expense": float(new_expense),
        },
        "transaction_count": len(transactions)
    }


@router.post("/apply")
async def apply_currency_conversion(
    new_currency: str,
    confirm: bool = False,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Apply currency conversion to all transactions.
    Requires confirm=true to actually perform the conversion.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Please confirm the conversion by setting confirm=true"
        )
    
    # Get current user
    user = await UserService.get_by_id(db, current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_currency = user.currency
    
    if current_currency == new_currency:
        raise HTTPException(
            status_code=400,
            detail=f"Already using {new_currency}"
        )
    
    # Get exchange rate
    rate = await CurrencyService.get_exchange_rate(current_currency, new_currency)
    if not rate:
        raise HTTPException(
            status_code=503,
            detail=f"Could not get exchange rate"
        )
    
    # TODO: Implement actual conversion of all transactions
    # For now, just update user's currency preference
    # In a real implementation, you might want to:
    # 1. Create a conversion history record
    # 2. Update all transaction amounts
    # 3. Or store amounts in a base currency and convert on-the-fly
    
    # Update user's currency
    update_data = UserUpdate(currency=new_currency)
    await UserService.update(db, user, update_data)
    
    return {
        "message": f"Currency changed from {current_currency} to {new_currency}",
        "rate_applied": rate,
        "note": "All future transactions will use the new currency"
    }
