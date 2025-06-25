import enum
from sqlalchemy import (Column, Integer, String, Boolean, Date, Text,
                      ForeignKey, DateTime, Numeric, Enum, func, JSON)
from sqlalchemy.orm import relationship
from database import Base


class CategoryEnum(str, enum.Enum):
    FOOD = "Food"
    TRAVEL = "Travel"
    ENTERTAINMENT = "Entertainment"
    HOUSEHOLD_BILL = "Household Bill"
    OTHER = "Other"


class ProcessingStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class ApprovalStatusEnum(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    profile_image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    expenses = relationship("Expense", back_populates="owner")
    email_accounts = relationship("EmailAccount", back_populates="user")
    transaction_approvals = relationship("TransactionApproval", back_populates="user")


class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email_address = Column(String(255), nullable=False, index=True)
    # Encrypted OAuth credentials stored as JSON
    oauth_credentials = Column(Text, nullable=True)  # Will be encrypted
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_successful_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_in_progress = Column(Boolean, default=False)
    sync_task_id = Column(String(255), nullable=True)  # Current sync task ID
    sync_error_count = Column(Integer, default=0)
    last_sync_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="email_accounts")
    email_messages = relationship("EmailMessage", back_populates="email_account")


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True, index=True)
    email_account_id = Column(Integer, ForeignKey("email_accounts.id"), nullable=False)
    message_id = Column(String(255), nullable=False, index=True)  # Gmail message ID
    thread_id = Column(String(255), nullable=True, index=True)  # Gmail thread ID for conversation grouping
    subject = Column(String(500), nullable=True)
    sender = Column(String(255), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_status = Column(Enum(ProcessingStatusEnum), default=ProcessingStatusEnum.PENDING)
    has_attachments = Column(Boolean, default=False)
    thread_message_count = Column(Integer, nullable=True, default=1)  # Number of messages in this thread
    is_thread_root = Column(Boolean, nullable=True, default=True)  # True if this is the first message in thread
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    email_account = relationship("EmailAccount", back_populates="email_messages")
    transaction_approvals = relationship("TransactionApproval", back_populates="email_message")
    expenses = relationship("Expense", back_populates="email_message")


class TransactionApproval(Base):
    __tablename__ = "transaction_approvals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email_message_id = Column(Integer, ForeignKey("email_messages.id"), nullable=True)
    # Store extracted OCR data as JSON
    extracted_data = Column(JSON, nullable=True)
    approval_status = Column(Enum(ApprovalStatusEnum), default=ApprovalStatusEnum.PENDING)
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="transaction_approvals")
    email_message = relationship("EmailMessage", back_populates="transaction_approvals")
    expenses = relationship("Expense", back_populates="transaction_approval")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    merchant_name = Column(String, index=True)
    date = Column(Date, nullable=False)
    # Using Numeric for precise currency handling
    amount = Column(Numeric(10, 2), nullable=False) 
    currency = Column(String, default='NPR', nullable=False)
    category = Column(Enum(CategoryEnum), nullable=True) # Nullable as per OCR flow in PRD
    is_ocr_entry = Column(Boolean, default=False)
    ocr_raw_text = Column(Text, nullable=True)
    # Email-related fields
    email_message_id = Column(Integer, ForeignKey("email_messages.id"), nullable=True)
    transaction_approval_id = Column(Integer, ForeignKey("transaction_approvals.id"), nullable=True)
    extraction_confidence = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="expenses")
    email_message = relationship("EmailMessage", back_populates="expenses")
    transaction_approval = relationship("TransactionApproval", back_populates="expenses")