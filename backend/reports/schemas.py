from pydantic import BaseModel
from datetime import date
from decimal import Decimal

from models import CategoryEnum # Import Enum from DB models

class ReportExpenseItem(BaseModel):
    """Schema for items returned in the report data."""
    merchant_name: str
    date: date
    amount: Decimal 
    currency: str
    category: CategoryEnum

    class Config:
        from_attributes = True # Enable ORM mode 