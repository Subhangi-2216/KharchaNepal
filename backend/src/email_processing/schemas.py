"""
Pydantic schemas for email processing API.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, Dict, Any
from models import ProcessingStatusEnum, ApprovalStatusEnum


class EmailAccountBase(BaseModel):
    """Base schema for email account."""
    email_address: EmailStr
    is_active: bool = True


class EmailAccountCreate(EmailAccountBase):
    """Schema for creating an email account."""
    oauth_credentials: str  # Encrypted credentials


class EmailAccountResponse(EmailAccountBase):
    """Schema for email account response."""
    id: int
    user_id: int
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailMessageBase(BaseModel):
    """Base schema for email message."""
    message_id: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    received_at: datetime
    has_attachments: bool = False


class EmailMessageResponse(EmailMessageBase):
    """Schema for email message response."""
    id: int
    email_account_id: int
    processed_at: Optional[datetime] = None
    processing_status: ProcessingStatusEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionApprovalBase(BaseModel):
    """Base schema for transaction approval."""
    extracted_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class TransactionApprovalCreate(TransactionApprovalBase):
    """Schema for creating a transaction approval."""
    email_message_id: Optional[int] = None


class TransactionApprovalResponse(TransactionApprovalBase):
    """Schema for transaction approval response."""
    id: int
    user_id: int
    email_message_id: Optional[int] = None
    approval_status: ApprovalStatusEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionApprovalUpdate(BaseModel):
    """Schema for updating transaction approval."""
    approval_status: ApprovalStatusEnum
    extracted_data: Optional[Dict[str, Any]] = None


class OAuthCallbackResponse(BaseModel):
    """Schema for OAuth callback response."""
    success: bool
    message: str
    email_address: Optional[str] = None


class EmailSyncRequest(BaseModel):
    """Schema for email sync request."""
    force_full_sync: bool = False
    days_back: int = Field(default=7, ge=1, le=30)


class EmailSyncResponse(BaseModel):
    """Schema for email sync response."""
    task_id: str
    status: str
    message: str
    account_id: int
