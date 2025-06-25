"""
Pydantic schemas for OCR-related requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class OCRRequest(BaseModel):
    """Schema for OCR request."""
    file_id: str = Field(..., description="ID of the uploaded file to process")


class OCRTextResult(BaseModel):
    """Schema for raw OCR text result."""
    text: str = Field(..., description="Raw text extracted from the image")
    confidence: float = Field(..., description="Confidence score of the OCR result")


class ExtractedField(BaseModel):
    """Schema for a single extracted field from OCR text."""
    name: str = Field(..., description="Name of the extracted field")
    value: str = Field(..., description="Value of the extracted field")
    confidence: float = Field(..., description="Confidence score for this extraction")


class OCRProcessedResult(BaseModel):
    """Schema for processed OCR result with extracted fields."""
    raw_text: str = Field(..., description="Raw text extracted from the image")
    extracted_fields: List[ExtractedField] = Field(
        ..., description="List of extracted fields from the receipt"
    )
    merchant_name: Optional[str] = Field(None, description="Extracted merchant name")
    total_amount: Optional[float] = Field(None, description="Extracted total amount")
    date: Optional[datetime] = Field(None, description="Extracted date of transaction")
    items: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of extracted line items if available"
    )
    image_path: str = Field(..., description="Path to the processed image")


class OCRResponse(BaseModel):
    """Schema for OCR response."""
    success: bool = Field(..., description="Whether OCR processing was successful")
    message: str = Field(..., description="Status message")
    result: Optional[OCRProcessedResult] = Field(
        None, description="Processed OCR result if successful"
    )