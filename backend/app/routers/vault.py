"""Vault API endpoints for financial portfolio management."""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.vault_service import VaultService
from app.schemas.vault import (
    VaultAccountCreate, VaultAccountUpdate, VaultAccountResponse,
    VaultSummary, VaultProjectionRequest, VaultProjectionResponse,
    VaultProjectionSettingsUpdate, VaultProjectionSettingsResponse
)

router = APIRouter(prefix="/vault", tags=["vault"])


@router.get("/accounts", response_model=List[VaultAccountResponse])
async def get_accounts(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get all vault accounts for current user."""
    accounts = await VaultService.get_accounts(db, current_user_id)
    return accounts


@router.post("/accounts", response_model=VaultAccountResponse)
async def create_account(
    data: VaultAccountCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create new vault account."""
    account = await VaultService.create_account(db, current_user_id, data)
    return account


@router.patch("/accounts/{account_id}", response_model=VaultAccountResponse)
async def update_account(
    account_id: int,
    data: VaultAccountUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update vault account."""
    account = await VaultService.get_account(db, account_id, current_user_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    updated = await VaultService.update_account(db, account, data)
    return updated


@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete vault account."""
    account = await VaultService.get_account(db, account_id, current_user_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    await VaultService.delete_account(db, account)
    return {"message": "Account deleted"}


@router.get("/summary", response_model=VaultSummary)
async def get_summary(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get vault summary (total assets, liabilities, net worth)."""
    accounts = await VaultService.get_accounts(db, current_user_id)
    summary = VaultService.calculate_summary(accounts)
    return summary


@router.post("/projection", response_model=VaultProjectionResponse)
async def get_projection(
    request: VaultProjectionRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get financial projection over time."""
    accounts = await VaultService.get_accounts(db, current_user_id)
    
    # Use provided values or fall back to settings from DB
    monthly_income = request.estimated_monthly_income
    monthly_expenses = request.estimated_monthly_expenses
    
    if not accounts and (monthly_income is None or monthly_expenses is None):
        return VaultProjectionResponse(
            projection=[],
            summary=VaultSummary(total_assets=0, total_liabilities=0, net_worth=0),
            milestones=[]
        )
    
    projection, milestones = VaultService.calculate_projection(
        accounts, request.period, request.include_reinvestment,
        monthly_income=monthly_income or Decimal("0"),
        monthly_expenses=monthly_expenses or Decimal("0")
    )
    summary = VaultService.calculate_summary(accounts)
    
    return VaultProjectionResponse(
        projection=projection,
        summary=summary,
        milestones=milestones
    )


@router.get("/settings", response_model=VaultProjectionSettingsResponse)
async def get_settings(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get vault projection settings."""
    from app.models.vault import VaultProjectionSettings
    from sqlalchemy import select
    
    result = await db.execute(
        select(VaultProjectionSettings).where(
            VaultProjectionSettings.user_id == current_user_id
        )
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Return default settings
        return VaultProjectionSettingsResponse(
            id=0,
            user_id=current_user_id,
            default_projection_period="1_year",
            reinvest_deposits="to_checking",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    return settings


@router.patch("/settings", response_model=VaultProjectionSettingsResponse)
async def update_settings(
    data: VaultProjectionSettingsUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update vault projection settings."""
    from app.models.vault import VaultProjectionSettings
    from sqlalchemy import select
    from datetime import datetime
    
    result = await db.execute(
        select(VaultProjectionSettings).where(
            VaultProjectionSettings.user_id == current_user_id
        )
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create new settings
        settings = VaultProjectionSettings(
            user_id=current_user_id,
            estimated_monthly_income=data.estimated_monthly_income,
            estimated_monthly_expenses=data.estimated_monthly_expenses,
            default_projection_period=data.default_projection_period or "1_year",
            reinvest_deposits=data.reinvest_deposits or "to_checking"
        )
        db.add(settings)
    else:
        # Update existing
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        settings.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(settings)
    return settings
