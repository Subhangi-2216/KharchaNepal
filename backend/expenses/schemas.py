from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from models import CategoryEnum # Import Enum from DB models

# Base properties shared by all expense schemas
class ExpenseBase(BaseModel):
    merchant_name: str = Field(..., min_length=1)
    date: date
    amount: Decimal = Field(..., gt=0) # Amount must be greater than 0
    category: CategoryEnum # Use the enum for validation

# Properties required for creating an expense via API
class ExpenseCreate(ExpenseBase):
    pass

# Properties to return to the client
class Expense(ExpenseBase):
    id: int
    user_id: int
    currency: str
    is_ocr_entry: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Enable ORM mode for Pydantic v2 