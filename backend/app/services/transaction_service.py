from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List, Tuple
from decimal import Decimal
from datetime import datetime

from app.models.transaction import Transaction, TransactionType, TransactionSource
from app.services.category_service import CategoryService
from app.schemas.transaction import TransactionCreate, TransactionFilter


class TransactionService:
    @staticmethod
    async def get_by_id(db: AsyncSession, transaction_id: int, user_id: int) -> Optional[Transaction]:
        result = await db.execute(
            select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(
        db: AsyncSession, 
        user_id: int, 
        filters: TransactionFilter
    ) -> Tuple[List[Transaction], int]:
        query = select(Transaction).where(Transaction.user_id == user_id)
        count_query = select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
        
        if filters.type:
            query = query.where(Transaction.type == filters.type)
            count_query = count_query.where(Transaction.type == filters.type)
        
        if filters.date_from:
            query = query.where(Transaction.transaction_date >= filters.date_from)
            count_query = count_query.where(Transaction.transaction_date >= filters.date_from)
        
        if filters.date_to:
            query = query.where(Transaction.transaction_date <= filters.date_to)
            count_query = count_query.where(Transaction.transaction_date <= filters.date_to)
        
        if filters.category_id:
            query = query.where(Transaction.category_id == filters.category_id)
            count_query = count_query.where(Transaction.category_id == filters.category_id)
        
        # Order by transaction_date desc
        query = query.order_by(desc(Transaction.transaction_date))
        
        # Pagination
        query = query.offset(filters.offset).limit(filters.limit)
        
        result = await db.execute(query)
        count_result = await db.execute(count_query)
        
        return result.scalars().all(), count_result.scalar()

    @staticmethod
    async def create(db: AsyncSession, transaction_data: TransactionCreate, user_id: int) -> Transaction:
        # Get or create category
        category = await CategoryService.get_or_create(db, transaction_data.category_name, user_id)
        
        # Convert string type to Enum if needed
        transaction_type = transaction_data.type
        if isinstance(transaction_type, str):
            transaction_type = TransactionType(transaction_type)
        
        transaction = Transaction(
            user_id=user_id,
            type=transaction_type,
            amount=transaction_data.amount,
            category_id=category.id,
            category_name=category.name,
            description=transaction_data.description,
            transaction_date=transaction_data.transaction_date,
            source=TransactionSource.MANUAL
        )
        
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction

    @staticmethod
    async def delete(db: AsyncSession, transaction_id: int, user_id: int) -> bool:
        transaction = await TransactionService.get_by_id(db, transaction_id, user_id)
        if not transaction:
            return False
        
        await db.delete(transaction)
        await db.commit()
        return True

    @staticmethod
    async def get_recent(db: AsyncSession, user_id: int, limit: int = 5) -> List[Transaction]:
        result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(desc(Transaction.transaction_date))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_totals(
        db: AsyncSession, 
        user_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        period: Optional[str] = None
    ) -> Tuple[Decimal, Decimal]:
        """Returns (total_income, total_expense)"""
        query_income = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.INCOME
        )
        query_expense = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE
        )
        
        if date_from:
            query_income = query_income.where(Transaction.transaction_date >= date_from)
            query_expense = query_expense.where(Transaction.transaction_date >= date_from)
        
        if date_to:
            query_income = query_income.where(Transaction.transaction_date <= date_to)
            query_expense = query_expense.where(Transaction.transaction_date <= date_to)
        
        # Handle period shortcuts
        if period == "month":
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query_income = query_income.where(Transaction.transaction_date >= month_start)
            query_expense = query_expense.where(Transaction.transaction_date >= month_start)
        elif period == "year":
            now = datetime.utcnow()
            year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            query_income = query_income.where(Transaction.transaction_date >= year_start)
            query_expense = query_expense.where(Transaction.transaction_date >= year_start)
        
        income_result = await db.execute(query_income)
        expense_result = await db.execute(query_expense)
        
        total_income = income_result.scalar() or Decimal("0")
        total_expense = expense_result.scalar() or Decimal("0")
        
        return total_income, total_expense

    @staticmethod
    async def get_by_category(
        db: AsyncSession,
        user_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        period: Optional[str] = None
    ) -> List[dict]:
        """Returns expenses grouped by category"""
        query = select(
            Transaction.category_name,
            func.sum(Transaction.amount).label("total")
        ).where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE
        ).group_by(Transaction.category_name)
        
        if date_from:
            query = query.where(Transaction.transaction_date >= date_from)
        if date_to:
            query = query.where(Transaction.transaction_date <= date_to)
        
        # Handle period shortcuts
        if period == "month":
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.where(Transaction.transaction_date >= month_start)
        elif period == "year":
            now = datetime.utcnow()
            year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.where(Transaction.transaction_date >= year_start)
        
        query = query.order_by(desc("total"))
        
        result = await db.execute(query)
        return [{"category": row[0], "amount": row[1]} for row in result.all()]
