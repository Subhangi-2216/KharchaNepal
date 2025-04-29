from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from database import get_db
from models import User
from auth import service as auth_service
from auth import schemas as auth_schemas

# OAuth2 scheme definition
# tokenUrl should match the path of your login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login") 

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """Dependency to get the current authenticated user from JWT token."""
    print(f"--- get_current_user: Received token: {token[:10]}...{token[-10:]}") # DEBUG
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = auth_service.decode_access_token(token)
    print(f"--- get_current_user: Decoded payload: {payload}") # DEBUG
    if payload is None:
        print("--- get_current_user: Payload is None, raising 401") # DEBUG
        raise credentials_exception

    email: Optional[str] = payload.get("sub") # Assuming email is stored in 'sub' claim
    print(f"--- get_current_user: Email from payload: {email}") # DEBUG
    if email is None:
        print("--- get_current_user: Email is None, raising 401") # DEBUG
        raise credentials_exception

    token_data = auth_schemas.TokenData(email=email)

    # Call the service function to get the user
    print(f"--- get_current_user: Looking up user by email: {token_data.email}") # DEBUG
    user = await auth_service.get_user_by_email(db, email=token_data.email)
    print(f"--- get_current_user: User found in DB: {'Yes (ID: '+str(user.id)+')' if user else 'No'}") # DEBUG
    if user is None:
        print("--- get_current_user: User not found in DB, raising 401") # DEBUG
        raise credentials_exception

    print(f"--- get_current_user: Returning user object (ID: {user.id})") # DEBUG
    return user

# Optional: Dependency to get the current active user (can add is_active checks later)
async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user 