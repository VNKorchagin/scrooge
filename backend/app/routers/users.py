"""Router for user management (admin and self-service)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.schemas.user import User as UserSchema, UserAdminView, UserDeleteRequest
from app.services.user_service import UserService

router = APIRouter()


def check_admin(current_user: User):
    """Check if user is admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_own_account(
    request: UserDeleteRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete own account.
    User must confirm the deletion.
    """
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please confirm account deletion"
        )
    
    user = await UserService.get_by_id(db, current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await UserService.soft_delete(db, user)
    return None


# Admin endpoints
@router.get("/admin/users", response_model=List[UserAdminView])
async def list_all_users(
    include_deleted: bool = False,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users (admin only).
    Optionally include soft-deleted users.
    """
    current_user = await UserService.get_by_id(db, current_user_id)
    check_admin(current_user)
    
    users = await UserService.get_all(db, include_inactive=include_deleted)
    
    # Enrich with stats
    result = []
    for user in users:
        stats = await UserService.get_user_stats(db, user.id)
        user_dict = {
            "id": user.id,
            "username": user.username,
            "language": user.language,
            "currency": user.currency,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "is_deleted": user.is_deleted,
            **stats
        }
        result.append(user_dict)
    
    return result


@router.get("/admin/users/{user_id}", response_model=UserAdminView)
async def get_user_details(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific user (admin only)."""
    current_user = await UserService.get_by_id(db, current_user_id)
    check_admin(current_user)
    
    user = await UserService.get_by_id(db, user_id, include_inactive=True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    stats = await UserService.get_user_stats(db, user.id)
    return {
        "id": user.id,
        "username": user.username,
        "language": user.language,
        "currency": user.currency,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": user.created_at,
        "is_deleted": user.is_deleted,
        **stats
    }


@router.post("/admin/users/{user_id}/restore", response_model=UserSchema)
async def restore_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Restore a soft-deleted user (admin only)."""
    current_user = await UserService.get_by_id(db, current_user_id)
    check_admin(current_user)
    
    user = await UserService.get_by_id(db, user_id, include_inactive=True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_active:
        raise HTTPException(status_code=400, detail="User is not deleted")
    
    restored_user = await UserService.restore(db, user)
    return restored_user


@router.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: int,
    hard_delete: bool = False,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a user (admin only).
    
    - soft delete by default (hard_delete=false)
    - hard delete removes all data permanently (hard_delete=true)
    """
    current_user = await UserService.get_by_id(db, current_user_id)
    check_admin(current_user)
    
    # Prevent self-deletion through admin endpoint
    if user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself through admin endpoint"
        )
    
    user = await UserService.get_by_id(db, user_id, include_inactive=True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if hard_delete:
        await UserService.hard_delete(db, user)
    else:
        await UserService.soft_delete(db, user)
    
    return None


@router.post("/admin/users/{user_id}/make-admin", response_model=UserSchema)
async def make_user_admin(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Grant admin privileges to a user (admin only)."""
    current_user = await UserService.get_by_id(db, current_user_id)
    check_admin(current_user)
    
    user = await UserService.get_by_id(db, user_id, include_inactive=True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_admin = True
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/admin/users/{user_id}/revoke-admin", response_model=UserSchema)
async def revoke_admin_privileges(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Revoke admin privileges from a user (admin only)."""
    current_user = await UserService.get_by_id(db, current_user_id)
    check_admin(current_user)
    
    # Prevent revoking your own admin privileges
    if user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke your own admin privileges"
        )
    
    user = await UserService.get_by_id(db, user_id, include_inactive=True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_admin = False
    await db.commit()
    await db.refresh(user)
    return user
