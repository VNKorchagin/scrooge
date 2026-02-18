from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List

from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    @staticmethod
    async def get_by_username(db: AsyncSession, username: str, include_inactive: bool = False) -> Optional[User]:
        query = select(User).where(User.username == username)
        if not include_inactive:
            query = query.where(User.is_active == True)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int, include_inactive: bool = False) -> Optional[User]:
        user = await db.get(User, user_id)
        if user and not include_inactive and not user.is_active:
            return None
        return user

    @staticmethod
    async def get_all(db: AsyncSession, include_inactive: bool = False) -> List[User]:
        query = select(User)
        if not include_inactive:
            query = query.where(User.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate) -> User:
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            hashed_password=hashed_password,
            currency=user_data.currency
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def update(db: AsyncSession, user: User, update_data: UserUpdate) -> User:
        """Update user settings."""
        if update_data.language is not None:
            user.language = update_data.language
        if update_data.currency is not None:
            user.currency = update_data.currency
        
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def soft_delete(db: AsyncSession, user: User) -> User:
        """Soft delete a user (mark as inactive)."""
        user.is_active = False
        user.deleted_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def restore(db: AsyncSession, user: User) -> User:
        """Restore a soft-deleted user."""
        user.is_active = True
        user.deleted_at = None
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def hard_delete(db: AsyncSession, user: User) -> None:
        """Permanently delete a user and all associated data."""
        await db.delete(user)
        await db.commit()

    @staticmethod
    async def get_user_stats(db: AsyncSession, user_id: int) -> dict:
        """Get statistics for a user (for admin view)."""
        from sqlalchemy import func
        
        # Count transactions
        result = await db.execute(
            select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
        )
        transaction_count = result.scalar() or 0
        
        # Calculate totals
        result = await db.execute(
            select(func.sum(Transaction.amount))
            .where(Transaction.user_id == user_id, Transaction.type == TransactionType.INCOME)
        )
        total_income = float(result.scalar() or 0)
        
        result = await db.execute(
            select(func.sum(Transaction.amount))
            .where(Transaction.user_id == user_id, Transaction.type == TransactionType.EXPENSE)
        )
        total_expense = float(result.scalar() or 0)
        
        return {
            "transaction_count": transaction_count,
            "total_income": total_income,
            "total_expense": total_expense
        }

    @staticmethod
    async def authenticate(db: AsyncSession, username: str, password: str) -> Optional[User]:
        user = await UserService.get_by_username(db, username)
        if not user:
            return None
        if not user.is_active:
            return None  # Cannot login if account is deleted
        if not verify_password(password, user.hashed_password):
            return None
        return user
