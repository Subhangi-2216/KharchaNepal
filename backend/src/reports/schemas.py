from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional
from decimal import Decimal # Import Decimal for amount

from models import CategoryEnum # Assuming CategoryEnum is accessible here

class ReportFilters(BaseModel):
    startDate: date
    endDate: date
    categories: Optional[List[CategoryEnum]] = None # Optional list of categories

# Add the ExpenseReportItem schema
class ExpenseReportItem(BaseModel):
    merchant_name: Optional[str] = None # Allow null as per model
    date: date
    amount: Decimal # Keep as Decimal for precision in API response
    currency: str
    category: Optional[CategoryEnum] = None # Allow null as per model

    class Config:
        from_attributes = True # Enable ORM mode for validation from Expense model 