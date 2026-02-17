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
from app.schemas.transaction import TransactionFilter
from app.models.transaction import TransactionType

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
    filters = TransactionFilter(
        type=type,
        date_from=date_from,
        date_to=date_to,
        limit=10000,  # High limit for export
        offset=0
    )
    
    transactions, _ = await TransactionService.get_list(db, current_user_id, filters)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "Type", "Amount", "Category", "Description", 
        "Transaction Date", "Source", "Created At"
    ])
    
    # Write data
    for t in transactions:
        writer.writerow([
            t.id,
            t.type.value,
            float(t.amount),
            t.category_name,
            t.description or "",
            t.transaction_date.isoformat(),
            t.source.value,
            t.created_at.isoformat()
        ])
    
    output.seek(0)
    
    filename = f"transactions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
