from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.category import Category, CategoryCreate
from app.services.category_service import CategoryService

router = APIRouter()


@router.get("", response_model=List[Category])
async def list_categories(
    q: Optional[str] = Query(None, description="Search query for category name"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get categories for current user.
    If 'q' is provided, returns filtered results for autocomplete (max 10).
    Otherwise returns all categories.
    """
    if q:
        return await CategoryService.search(db, current_user_id, q, limit=10)
    return await CategoryService.get_all(db, current_user_id)


@router.post("", response_model=Category)
async def create_category(
    category_data: CategoryCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new category (or return existing if name already exists)"""
    return await CategoryService.create(db, category_data, current_user_id)
