import io
import csv
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.transaction_service import TransactionService
from app.models.transaction import TransactionType, TransactionSource

router = APIRouter()


@router.get("/csv")
async def export_csv(
    type: Optional[TransactionType] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Export transactions to CSV format.
    """
    transactions = await TransactionService.get_all_for_export(
        db, current_user_id, type, date_from, date_to
    )
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header (ID, Type, Source removed; Amount includes sign)
    writer.writerow([
        "Amount", "Category", "Description", 
        "Transaction Date", "Created At"
    ])
    
    # Write data
    for t in transactions:
        # Amount: positive for income, negative for expense
        amount = float(t.amount) if t.amount else 0
        if t.type == TransactionType.expense:
            amount = -amount
        
        writer.writerow([
            amount,
            t.category_name or "",
            t.description or "",
            t.transaction_date.isoformat() if t.transaction_date else "",
            t.created_at.isoformat() if t.created_at else ""
        ])
    
    output.seek(0)
    
    filename = f"transactions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
