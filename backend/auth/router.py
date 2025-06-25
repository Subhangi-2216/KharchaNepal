from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User as UserModel # Avoid collision with schema
from auth import service as auth_service
from auth import schemas as auth_schemas
from auth import dependencies as auth_deps

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

@router.post("/register", response_model=auth_schemas.User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: auth_schemas.UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Handles user registration."""
    # Check if user already exists
    existing_user = await auth_service.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash the password
    hashed_password = auth_service.get_password_hash(user_in.password)

    # Create new user instance
    db_user = UserModel(
        email=user_in.email,
        name=user_in.name,
        hashed_password=hashed_password
    )

    # Add user to the database session and commit
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user

@router.post("/login", response_model=auth_schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Handles user login and returns a JWT access token."""
    user = await auth_service.get_user_by_email(db, email=form_data.username) # OAuth2 form uses 'username' field for email
    if not user or not auth_service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    access_token = auth_service.create_access_token(
        data={"sub": user.email} # Use email as subject in JWT
    )

    return {"access_token": access_token, "token_type": "bearer"}

# Example Protected Route
@router.get("/users/me", response_model=auth_schemas.User)
async def read_users_me(
    current_user: Annotated[UserModel, Depends(auth_deps.get_current_active_user)]
):
    """Fetches the current authenticated user's details."""
    return current_user 