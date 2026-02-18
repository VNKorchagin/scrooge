"""Vault models for financial portfolio tracking."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class AccountType(str, Enum):
    """Types of financial accounts."""
    CHECKING = "checking"  # Основной счет
    SAVINGS = "savings"    # Накопительный счет
    DEPOSIT = "deposit"    # Депозит
    BROKERAGE = "brokerage"  # Брокерский счет
    LOAN = "loan"          # Кредит


class VaultAccount(Base):
    """Base model for all vault accounts (assets and liabilities)."""
    __tablename__ = "vault_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Account identification
    name = Column(String(100), nullable=False)  # Название счета/депозита/кредита
    account_type = Column(SQLEnum(AccountType), nullable=False)
    
    # Balance information
    balance = Column(Numeric(15, 2), nullable=False, default=0)  # Текущий баланс
    currency = Column(String(3), default="USD")  # Валюта
    
    # Interest rate (for deposits, savings, loans)
    interest_rate = Column(Numeric(5, 2), nullable=True)  # Годовая ставка в %
    
    # For deposits and loans - end date
    end_date = Column(Date, nullable=True)  # Дата окончания депозита/кредита
    
    # For loans - monthly payment
    monthly_payment = Column(Numeric(15, 2), nullable=True)  # Ежемесячный платеж
    
    # Optional description
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="vault_accounts")
    
    def __repr__(self):
        return f"<VaultAccount(id={self.id}, name='{self.name}', type={self.account_type}, balance={self.balance})>"
    
    @property
    def is_asset(self) -> bool:
        """Check if this account is an asset (not a loan)."""
        return self.account_type != AccountType.LOAN
    
    @property
    def is_liability(self) -> bool:
        """Check if this account is a liability (loan)."""
        return self.account_type == AccountType.LOAN


class VaultSnapshot(Base):
    """Historical snapshots of vault totals for tracking progress."""
    __tablename__ = "vault_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Snapshot data
    snapshot_date = Column(Date, nullable=False, default=date.today)
    
    # Totals
    total_assets = Column(Numeric(15, 2), nullable=False, default=0)
    total_liabilities = Column(Numeric(15, 2), nullable=False, default=0)
    net_worth = Column(Numeric(15, 2), nullable=False, default=0)
    
    # Detailed breakdown
    checking_balance = Column(Numeric(15, 2), default=0)
    savings_balance = Column(Numeric(15, 2), default=0)
    deposits_balance = Column(Numeric(15, 2), default=0)
    brokerage_balance = Column(Numeric(15, 2), default=0)
    loans_balance = Column(Numeric(15, 2), default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="vault_snapshots")


class VaultProjectionSettings(Base):
    """User settings for vault projections."""
    __tablename__ = "vault_projection_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Monthly cash flow (for future AI recommendations)
    estimated_monthly_income = Column(Numeric(15, 2), nullable=True)
    estimated_monthly_expenses = Column(Numeric(15, 2), nullable=True)
    
    # Default projection period
    default_projection_period = Column(String(20), default="1_year")  # month, quarter, etc.
    
    # Reinvestment settings
    reinvest_deposits = Column(String(20), default="to_checking")  # to_checking, reinvest, distribute
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="vault_projection_settings")
