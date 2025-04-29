import enum
from sqlalchemy import (Column, Integer, String, Boolean, Date, Text, 
                      ForeignKey, DateTime, Numeric, Enum, func)
from sqlalchemy.orm import relationship
from database import Base


class CategoryEnum(str, enum.Enum):
    FOOD = "Food"
    TRAVEL = "Travel"
    ENTERTAINMENT = "Entertainment"
    HOUSEHOLD_BILL = "Household Bill"
    OTHER = "Other"


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="expenses") 