from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from decimal import Decimal

# For the largest expense detail
class LargestExpenseDetail(BaseModel):
    amount: Decimal
    category: Optional[str] = None # Category might be null
    merchant_name: Optional[str] = None # Merchant might be null

    class Config:
        from_attributes = True # Updated from orm_mode

# For the main dashboard stats (monthly total, largest expense)
class DashboardStats(BaseModel):
    monthly_total: Decimal = Field(default=0.0)
    largest_expense: Optional[LargestExpenseDetail] = None

# For the category summary (last 30 days)
class CategorySummaryItem(BaseModel):
    category: Optional[str] = "Uncategorized" # Use default if null
    total_amount: Decimal
    percentage: float # Calculate percentage

class DashboardSummary(BaseModel):
    summary: List[CategorySummaryItem]
    total_last_30_days: Decimal = Field(default=0.0) 