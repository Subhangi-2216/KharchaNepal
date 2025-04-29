from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    # Add other fields you might include in the token payload (e.g., user_id)
    # user_id: Optional[int] = None

# --- User Schemas ---

# Base User properties
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

# Properties required for user creation
class UserCreate(UserBase):
    password: str

# Properties stored in DB (excluding password)
class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Replaces orm_mode = True in Pydantic v2

# Properties to return to client (safe version)
class User(UserInDBBase):
    pass

# Properties stored in DB (including hashed password - not usually sent to client)
class UserInDB(UserInDBBase):
    hashed_password: str 