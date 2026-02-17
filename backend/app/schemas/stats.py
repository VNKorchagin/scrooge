from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from decimal import Decimal


class CategoryStat(BaseModel):
    category: str
    amount: Decimal
    percentage: float


class DashboardStats(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    by_category: List[CategoryStat]
    recent_transactions: List[dict]  # Will be populated from Transaction schema
