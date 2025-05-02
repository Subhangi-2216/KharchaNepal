# backend/src/expenses/schemas.py
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any

from models import CategoryEnum

# Base schema for common expense attributes
class ExpenseBase(BaseModel):
    merchant_name: Optional[str] = Field(None, max_length=255)
    date: date
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2) # Ensure positive amount
    currency: Optional[str] = Field("NPR", max_length=10)
    category: Optional[CategoryEnum] = None

# Schema for creating an expense (used by manual entry and potentially PUT)
class ExpenseCreate(ExpenseBase):
    # Category is required for manual creation
    category: CategoryEnum

# Schema for updating an expense (used by PUT /expenses/{id} after OCR)
class ExpenseUpdate(BaseModel):
    # Allow updating any of the fields, all optional
    merchant_name: Optional[str] = Field(None, max_length=255)
    date: Optional[date]
    amount: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    currency: Optional[str] = Field(None, max_length=10)
    category: Optional[CategoryEnum] = None # Primarily used to set category after OCR

# Schema representing an expense as stored in the DB (used for reading/returning)
class ExpenseInDB(ExpenseBase):
    id: int
    user_id: int
    is_ocr_entry: bool = False
    ocr_raw_text: Optional[str] = None
    # Timestamps can be added if needed from the model
    # created_at: datetime
    # updated_at: datetime

    class Config:
        from_attributes = True

# Schema for the response of the OCR endpoint
class ExtractedData(BaseModel):
    # Fields that OCR attempts to extract
    date: Optional[date] = None
    date_confidence: Optional[float] = None  # Confidence score for date extraction (0.0-1.0)
    merchant_name: Optional[str] = None
    merchant_confidence: Optional[float] = None  # For future use
    amount: Optional[Decimal] = None
    amount_confidence: Optional[float] = None  # For future use
    currency: Optional[str] = "NPR"

class ExpenseOCRResponse(BaseModel):
    expense_id: int # ID of the partially created expense
    extracted_data: ExtractedData
    missing_fields: List[str] # Fields OCR couldn't find (e.g., ["date", "amount", "category"])
    message: str