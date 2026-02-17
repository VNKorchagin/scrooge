from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user_id, get_password_hash
from app.core.config import settings
from app.schemas.user import UserCreate, UserLogin, Token, User, UserUpdate
from app.services.user_service import UserService

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    existing_user = await UserService.get_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create user
    user = await UserService.create(db, user_data)
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    
    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await UserService.authenticate(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.id})
    
    return Token(access_token=access_token)


@router.get("/me", response_model=User)
async def get_me(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    user = await UserService.get_by_id(db, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.patch("/me", response_model=User)
async def update_me(
    update_data: UserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update current user settings (language, currency)."""
    user = await UserService.get_by_id(db, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    updated_user = await UserService.update(db, user, update_data)
    return updated_user
