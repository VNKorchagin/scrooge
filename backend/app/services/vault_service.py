"""Vault service for financial portfolio management."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Tuple
from dateutil.relativedelta import relativedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.vault import VaultAccount, AccountType, VaultSnapshot, VaultProjectionSettings
from app.schemas.vault import (
    VaultAccountCreate, VaultAccountUpdate, VaultSummary, 
    ProjectionDataPoint, VaultProjectionRequest
)


class VaultService:
    """Service for managing vault accounts and projections."""
    
    PERIOD_MONTHS = {
        "month": 1,
        "quarter": 3,
        "half_year": 6,
        "1_year": 12,
        "3_years": 36,
        "5_years": 60,
    }
    
    @staticmethod
    async def get_accounts(db: AsyncSession, user_id: int) -> List[VaultAccount]:
        """Get all vault accounts for user."""
        result = await db.execute(
            select(VaultAccount).where(VaultAccount.user_id == user_id)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_account(db: AsyncSession, account_id: int, user_id: int) -> Optional[VaultAccount]:
        """Get single vault account."""
        result = await db.execute(
            select(VaultAccount).where(
                VaultAccount.id == account_id,
                VaultAccount.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_account(db: AsyncSession, user_id: int, data: VaultAccountCreate) -> VaultAccount:
        """Create new vault account."""
        account = VaultAccount(
            user_id=user_id,
            name=data.name,
            account_type=data.account_type,
            balance=data.balance,
            currency=data.currency,
            interest_rate=data.interest_rate,
            end_date=data.end_date,
            monthly_payment=data.monthly_payment,
            description=data.description
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return account
    
    @staticmethod
    async def update_account(
        db: AsyncSession, 
        account: VaultAccount, 
        data: VaultAccountUpdate
    ) -> VaultAccount:
        """Update vault account."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)
        await db.commit()
        await db.refresh(account)
        return account
    
    @staticmethod
    async def delete_account(db: AsyncSession, account: VaultAccount) -> None:
        """Delete vault account."""
        await db.delete(account)
        await db.commit()
    
    @staticmethod
    def calculate_summary(accounts: List[VaultAccount]) -> VaultSummary:
        """Calculate vault summary from accounts."""
        total_assets = Decimal("0")
        total_liabilities = Decimal("0")
        
        breakdown = {
            "checking": Decimal("0"),
            "savings": Decimal("0"),
            "deposits": Decimal("0"),
            "brokerage": Decimal("0"),
            "loans": Decimal("0"),
        }
        
        for account in accounts:
            if account.account_type == AccountType.LOAN:
                total_liabilities += account.balance
                breakdown["loans"] += account.balance
            else:
                total_assets += account.balance
                if account.account_type == AccountType.CHECKING:
                    breakdown["checking"] += account.balance
                elif account.account_type == AccountType.SAVINGS:
                    breakdown["savings"] += account.balance
                elif account.account_type == AccountType.DEPOSIT:
                    breakdown["deposits"] += account.balance
                elif account.account_type == AccountType.BROKERAGE:
                    breakdown["brokerage"] += account.balance
        
        return VaultSummary(
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            net_worth=total_assets - total_liabilities,
            checking_balance=breakdown["checking"],
            savings_balance=breakdown["savings"],
            deposits_balance=breakdown["deposits"],
            brokerage_balance=breakdown["brokerage"],
            loans_balance=breakdown["loans"]
        )
    
    @staticmethod
    def calculate_projection(
        accounts: List[VaultAccount],
        period: str,
        include_reinvestment: bool = True,
        monthly_income: Decimal = Decimal("0"),
        monthly_expenses: Decimal = Decimal("0")
    ) -> Tuple[List[ProjectionDataPoint], List[dict]]:
        """Calculate financial projection over time."""
        months = VaultService.PERIOD_MONTHS.get(period, 12)
        today = date.today()
        
        # Separate assets and liabilities
        assets = [a for a in accounts if a.account_type != AccountType.LOAN]
        loans = [a for a in accounts if a.account_type == AccountType.LOAN]
        
        # Find checking account for cash flow (or use first asset as proxy)
        checking_account = next(
            (a for a in assets if a.account_type == AccountType.CHECKING),
            assets[0] if assets else None
        )
        
        projection = []
        milestones = []
        
        # Monthly savings (income minus expenses)
        monthly_savings = monthly_income - monthly_expenses
        
        # Calculate month by month
        for month in range(months + 1):
            current_date = today + relativedelta(months=month)
            
            total_assets = Decimal("0")
            total_liabilities = Decimal("0")
            month_milestones = []
            
            # Calculate assets
            for asset in assets:
                value = VaultService._calculate_asset_value(
                    asset, current_date, today, include_reinvestment
                )
                
                # Add monthly cash flow to checking account
                # Only add savings from month 1 onwards (month 0 is current state)
                if month > 0 and asset == checking_account and monthly_savings > 0:
                    value += monthly_savings * month
                
                total_assets += value
                
                # Check for deposit maturity
                if (asset.account_type == AccountType.DEPOSIT and 
                    asset.end_date and 
                    asset.end_date.year == current_date.year and 
                    asset.end_date.month == current_date.month):
                    milestones.append({
                        "date": asset.end_date,
                        "type": "deposit_maturity",
                        "name": asset.name,
                        "amount": float(asset.balance),
                        "month": month
                    })
                    month_milestones.append({
                        "type": "deposit_maturity",
                        "name": asset.name
                    })
            
            # If no checking account but we have savings, add as virtual checking
            if not checking_account and month > 0 and monthly_savings > 0:
                total_assets += monthly_savings * month
            
            # Calculate liabilities (loans)
            for loan in loans:
                remaining = VaultService._calculate_loan_balance(loan, current_date, today)
                total_liabilities += remaining
                
                # Calculate payoff month if not already known
                payoff_month = VaultService._calculate_loan_payoff_month(loan)
                
                # Check for loan payoff milestone
                if month == payoff_month and payoff_month != float('inf'):
                    # Only add milestone once
                    payoff_key = f"loan_payoff_{loan.id}"
                    if not any(m.get("key") == payoff_key for m in milestones):
                        milestones.append({
                            "date": current_date,
                            "type": "loan_payoff",
                            "name": loan.name,
                            "month": month,
                            "key": payoff_key
                        })
                        month_milestones.append({
                            "type": "loan_payoff",
                            "name": loan.name
                        })
            
            projection.append(ProjectionDataPoint(
                date=current_date,
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                net_worth=total_assets - total_liabilities,
                milestones=month_milestones
            ))
        
        return projection, milestones
    
    @staticmethod
    def _calculate_asset_value(
        asset: VaultAccount, 
        target_date: date, 
        start_date: date,
        include_reinvestment: bool
    ) -> Decimal:
        """Calculate asset value at target date with compound interest."""
        if asset.account_type == AccountType.CHECKING:
            return asset.balance
        
        # For deposits that have matured
        if asset.account_type == AccountType.DEPOSIT and asset.end_date:
            if target_date >= asset.end_date:
                # After maturity, assume moved to checking or reinvested
                if include_reinvestment:
                    # Calculate final value at maturity
                    months_to_maturity = (
                        (asset.end_date.year - start_date.year) * 12 +
                        (asset.end_date.month - start_date.month)
                    )
                    return VaultService._apply_interest(
                        asset.balance, asset.interest_rate or 0, months_to_maturity
                    )
                else:
                    return asset.balance
        
        # Apply compound interest for savings and deposits
        months = (target_date.year - start_date.year) * 12 + (target_date.month - start_date.month)
        return VaultService._apply_interest(
            asset.balance, asset.interest_rate or 0, months
        )
    
    @staticmethod
    def _calculate_loan_balance(
        loan: VaultAccount, 
        target_date: date, 
        start_date: date
    ) -> Decimal:
        """Calculate remaining loan balance at target date."""
        if not loan.monthly_payment or loan.monthly_payment <= 0:
            return loan.balance
        
        months = (target_date.year - start_date.year) * 12 + (target_date.month - start_date.month)
        
        # Simple amortization (can be improved with actual amortization formula)
        if loan.interest_rate:
            monthly_rate = (loan.interest_rate / Decimal("100")) / 12
            # Amortization formula
            if monthly_rate > 0:
                remaining = loan.balance * ((1 + monthly_rate) ** months) - \
                           loan.monthly_payment * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            else:
                remaining = loan.balance - (loan.monthly_payment * months)
        else:
            remaining = loan.balance - (loan.monthly_payment * months)
        
        return max(Decimal("0"), remaining)
    
    @staticmethod
    def _calculate_loan_payoff_month(loan: VaultAccount) -> int:
        """Calculate how many months until loan is fully paid off."""
        if not loan.monthly_payment or loan.monthly_payment <= 0:
            return float('inf')  # Never pays off
        
        balance = loan.balance
        payment = loan.monthly_payment
        
        # Simple case: no interest
        if not loan.interest_rate or loan.interest_rate <= 0:
            return int((balance / payment).to_integral_value(rounding='ROUND_UP'))
        
        # With interest: iterate month by month
        monthly_rate = (loan.interest_rate / Decimal("100")) / 12
        months = 0
        max_months = 1200  # Cap at 100 years to prevent infinite loops
        
        while balance > 0 and months < max_months:
            interest = balance * monthly_rate
            principal_paid = payment - interest
            if principal_paid <= 0:
                # Payment doesn't cover interest, loan never pays off
                return float('inf')
            balance -= principal_paid
            months += 1
        
        return months if balance <= 0 else float('inf')
    
    @staticmethod
    def _apply_interest(principal: Decimal, annual_rate: Decimal, months: int) -> Decimal:
        """Apply compound interest."""
        if annual_rate <= 0 or months <= 0:
            return principal
        
        monthly_rate = (annual_rate / Decimal("100")) / 12
        return principal * ((1 + monthly_rate) ** months)
