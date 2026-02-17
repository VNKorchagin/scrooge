from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from decimal import Decimal

from app.services.transaction_service import TransactionService
from app.schemas.stats import DashboardStats, CategoryStat


class StatsService:
    @staticmethod
    async def get_dashboard_stats(
        db: AsyncSession,
        user_id: int,
        period: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> DashboardStats:
        # Calculate totals
        total_income, total_expense = await TransactionService.get_totals(
            db, user_id, date_from, date_to, period
        )
        balance = total_income - total_expense
        
        # Get expenses by category
        category_data = await TransactionService.get_by_category(
            db, user_id, date_from, date_to, period
        )
        
        # Calculate percentages
        by_category = []
        if total_expense > 0:
            for item in category_data:
                percentage = round(float(item["amount"] / total_expense * 100), 2)
                by_category.append(CategoryStat(
                    category=item["category"],
                    amount=item["amount"],
                    percentage=percentage
                ))
        
        # Get recent transactions
        recent = await TransactionService.get_recent(db, user_id, 5)
        recent_transactions = [
            {
                "id": t.id,
                "type": t.type.value,
                "amount": float(t.amount),
                "category_name": t.category_name,
                "description": t.description,
                "transaction_date": t.transaction_date.isoformat(),
            }
            for t in recent
        ]
        
        return DashboardStats(
            total_income=total_income,
            total_expense=total_expense,
            balance=balance,
            by_category=by_category,
            recent_transactions=recent_transactions
        )
