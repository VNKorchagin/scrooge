from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List

from app.models.category import Category
from app.schemas.category import CategoryCreate


class CategoryService:
    @staticmethod
    async def get_by_id(db: AsyncSession, category_id: int, user_id: int) -> Optional[Category]:
        result = await db.execute(
            select(Category).where(Category.id == category_id, Category.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str, user_id: int) -> Optional[Category]:
        result = await db.execute(
            select(Category).where(
                func.lower(Category.name) == func.lower(name),
                Category.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def search(db: AsyncSession, user_id: int, query: str, limit: int = 10) -> List[Category]:
        result = await db.execute(
            select(Category)
            .where(
                Category.user_id == user_id,
                Category.name.ilike(f"%{query}%")
            )
            .order_by(Category.name)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_all(db: AsyncSession, user_id: int) -> List[Category]:
        result = await db.execute(
            select(Category).where(Category.user_id == user_id).order_by(Category.name)
        )
        return result.scalars().all()

    @staticmethod
    async def get_or_create(db: AsyncSession, name: str, user_id: int) -> Category:
        category = await CategoryService.get_by_name(db, name, user_id)
        if category:
            return category
        
        category = Category(name=name.strip(), user_id=user_id)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def create(db: AsyncSession, category_data: CategoryCreate, user_id: int) -> Category:
        existing = await CategoryService.get_by_name(db, category_data.name, user_id)
        if existing:
            return existing
        
        category = Category(name=category_data.name.strip(), user_id=user_id)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category
