# backend/src/user_settings/schemas.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

# Schema for returning user profile data
class UserProfile(BaseModel):
    id: int
    name: Optional[str] = None
    email: EmailStr
    profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True # Pydantic v2 ORM mode / orm_mode = True for v1

# Schema for updating user profile (name, email)
# Note: profile_image_url is handled by the separate image upload endpoint
class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1) # Ensure name isn't empty if provided
    email: Optional[EmailStr] = None

# Schema for password update request
class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8) # Enforce min length 8
    confirm_new_password: str

    @field_validator('confirm_new_password') # Use field_validator for Pydantic v2
    @classmethod
    def passwords_match(cls, v: str, info):
        # Pydantic v2 validation context access
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('New passwords do not match')
        return v

# Schema for image upload response
class ProfileImageUpdateResponse(BaseModel):
    profile_image_url: str 