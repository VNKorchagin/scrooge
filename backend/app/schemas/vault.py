"""Pydantic schemas for Vault."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from app.models.vault import AccountType


# Base schemas
class VaultAccountBase(BaseModel):
    """Base schema for vault account."""
    name: str = Field(..., min_length=1, max_length=100)
    account_type: AccountType
    balance: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    end_date: Optional[date] = None
    monthly_payment: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None


class VaultAccountCreate(VaultAccountBase):
    """Schema for creating vault account."""
    pass


class VaultAccountUpdate(BaseModel):
    """Schema for updating vault account."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    balance: Optional[Decimal] = Field(None, ge=0)
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    end_date: Optional[date] = None
    monthly_payment: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None


class VaultAccountResponse(VaultAccountBase):
    """Schema for vault account response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    @property
    def is_asset(self) -> bool:
        return self.account_type != AccountType.LOAN
    
    @property
    def is_liability(self) -> bool:
        return self.account_type == AccountType.LOAN


# Vault summary schema
class VaultSummary(BaseModel):
    """Summary of user's vault."""
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    
    # Breakdown by type
    checking_balance: Decimal = Decimal("0")
    savings_balance: Decimal = Decimal("0")
    deposits_balance: Decimal = Decimal("0")
    brokerage_balance: Decimal = Decimal("0")
    loans_balance: Decimal = Decimal("0")


# Projection schemas
class ProjectionDataPoint(BaseModel):
    """Single point in projection timeline."""
    date: date
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    milestones: List[dict] = []  # Events like deposit maturity, loan payoff


class VaultProjectionRequest(BaseModel):
    """Request for vault projection."""
    period: str = Field(default="1_year", pattern="^(month|quarter|half_year|1_year|3_years|5_years)$")
    include_reinvestment: bool = True
    estimated_monthly_income: Optional[Decimal] = Field(None, ge=0)
    estimated_monthly_expenses: Optional[Decimal] = Field(None, ge=0)


class VaultProjectionResponse(BaseModel):
    """Response with vault projection."""
    projection: List[ProjectionDataPoint]
    summary: VaultSummary
    milestones: List[dict]  # Key events (deposit maturity, loan payoff)


# Settings schemas
class VaultProjectionSettingsBase(BaseModel):
    """Base settings schema."""
    estimated_monthly_income: Optional[Decimal] = None
    estimated_monthly_expenses: Optional[Decimal] = None
    default_projection_period: str = "1_year"
    reinvest_deposits: str = "to_checking"


class VaultProjectionSettingsUpdate(BaseModel):
    """Schema for updating settings."""
    estimated_monthly_income: Optional[Decimal] = None
    estimated_monthly_expenses: Optional[Decimal] = None
    default_projection_period: Optional[str] = None
    reinvest_deposits: Optional[str] = None


class VaultProjectionSettingsResponse(VaultProjectionSettingsBase):
    """Schema for settings response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
