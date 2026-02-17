from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.stats import DashboardStats
from app.services.stats_service import StatsService

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    period: Optional[str] = Query("month", description="Period: month, year, or all"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard statistics.
    
    - period: 'month' (default), 'year', or 'all'
    - date_from/date_to: custom date range (overrides period if both provided)
    """
    # Handle 'all' period
    effective_period = None if period == "all" else period
    
    return await StatsService.get_dashboard_stats(
        db, current_user_id, effective_period, date_from, date_to
    )
