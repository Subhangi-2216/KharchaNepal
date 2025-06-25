# backend/src/user_settings/router.py
import os
import shutil
import uuid
from pathlib import Path
from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile,
    File, status, Form
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import User
from src.auth.dependencies import get_current_active_user
from src.auth import service as auth_service # Assumes auth service has get_user_by_email, verify_password, get_password_hash
from .schemas import (
    UserProfile, ProfileUpdate, PasswordUpdate,
    ProfileImageUpdateResponse
)

router = APIRouter(
    prefix="/api/user",
    tags=["User Settings"],
    dependencies=[Depends(get_current_active_user)], # Secure all endpoints in this router
    responses={404: {"description": "Not found"}},
)

# --- Configuration for Uploads ---
# Define the base directory relative to the backend root (where main.py is)
# Ensure this matches the StaticFiles mount in main.py
UPLOAD_DIR_BASE = Path("uploads")
PROFILE_IMAGE_DIR = UPLOAD_DIR_BASE / "profile_images"
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 # 2 MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Ensure upload directory exists (FastAPI runs from where you launch uvicorn, usually backend/)
PROFILE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)


# --- Helper Function for Filename ---
def get_unique_filename(user_id: int, original_filename: str) -> Path:
    """Generates a unique filename Path object preserving the extension and validates it."""
    if not original_filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename.")

    _, ext = os.path.splitext(original_filename)
    ext = ext.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )
    # Use UUID for randomness + user ID for potential organization/debugging
    unique_id = uuid.uuid4()
    # Return a Path object for easier handling
    return Path(f"user_{user_id}_{unique_id}{ext}")


# --- Endpoint Implementations ---

@router.get("/profile", response_model=UserProfile)
async def read_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    """Fetches the current authenticated user's profile details."""
    # User object from dependency is already up-to-date if token is valid
    return current_user

@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Updates the current authenticated user's name and/or email.
    Profile image is updated via the POST /profile/image endpoint.
    """
    update_data = profile_data.model_dump(exclude_unset=True) # Get only fields that were provided
    changes_made = False

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")

    # Check email uniqueness if email is being updated
    new_email = update_data.get("email")
    if new_email and new_email != current_user.email:
        existing_user = await auth_service.get_user_by_email(db, email=new_email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered by another user."
            )
        current_user.email = new_email
        changes_made = True

    # Update name if provided and different
    new_name = update_data.get("name")
    # Handle explicit null vs not provided vs empty string
    if profile_data.name is not None: # Check if name was present in the request payload
        if new_name is None: # If it resolved to None (e.g., empty string potentially)
             # Allow setting name to null if DB/model allows it.
             # If you don't want null names, add validation here or in schema.
             if current_user.name is not None:
                 current_user.name = None
                 changes_made = True
        elif new_name != current_user.name:
             current_user.name = new_name
             changes_made = True


    if changes_made:
        try:
            await db.commit()
            await db.refresh(current_user)
        except Exception as e:
            await db.rollback()
            print(f"Error updating profile for user {current_user.id}: {e}") # Basic logging
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not update profile information."
            )

    return current_user


@router.post("/profile/image", response_model=ProfileImageUpdateResponse)
async def upload_profile_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Uploads and updates the user's profile image."""
    if not file or not file.filename:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded or filename missing.")

    # Check file size before reading the whole thing into memory if possible
    # Use file.seek(0, 2) to get size, then file.seek(0)
    file.file.seek(0, 2) # Move to end of file
    file_size = file.file.tell() # Get position (size)
    await file.seek(0) # Move back to start for reading
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size is {MAX_FILE_SIZE_BYTES // 1024 // 1024}MB."
        )

    try:
        # Generate unique filename (Path object) and validate extension
        unique_filename = get_unique_filename(current_user.id, file.filename)
        file_path = PROFILE_IMAGE_DIR / unique_filename
        # Construct the URL path relative to the static mount point
        # IMPORTANT: This assumes UPLOAD_DIR_BASE ('uploads') is mounted at '/uploads'
        relative_url_path = f"/uploads/profile_images/{unique_filename.name}"

        # Save the file asynchronously if possible, otherwise use shutil
        # Using shutil.copyfileobj is generally safe and efficient for files
        try:
            with open(file_path, "wb") as buffer:
                 shutil.copyfileobj(file.file, buffer)
        except IOError as e:
             print(f"Error saving file {file_path}: {e}")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save uploaded file.")


        # --- Optional: Delete old image if it exists ---
        old_image_path_str = current_user.profile_image_url
        if old_image_path_str:
             # Convert URL path back to file system path (relative to backend root)
             # Example: "/uploads/profile_images/user_1_uuid.jpg" -> "uploads/profile_images/user_1_uuid.jpg"
             old_image_fs_path = Path(old_image_path_str.lstrip('/'))
             if old_image_fs_path.exists() and old_image_fs_path.is_file():
                 try:
                     old_image_fs_path.unlink()
                     print(f"Deleted old profile image: {old_image_fs_path}")
                 except OSError as e:
                     print(f"Error deleting old profile image {old_image_fs_path}: {e}") # Log error but continue

        # Update user profile in DB with the new relative URL path
        current_user.profile_image_url = relative_url_path
        await db.commit()
        await db.refresh(current_user)

        return ProfileImageUpdateResponse(profile_image_url=relative_url_path)

    except HTTPException as e:
        # If validation failed (filename/type/size), delete temp file if created
        if 'file_path' in locals() and file_path.exists():
             file_path.unlink(missing_ok=True)
        raise e # Re-raise validation or file save errors
    except Exception as e:
        await db.rollback()
        print(f"Error uploading profile image for user {current_user.id}: {e}")
        # Attempt to delete partially saved file if error occurred after saving but before DB commit
        if 'file_path' in locals() and file_path.exists():
             file_path.unlink(missing_ok=True) # Use missing_ok=True
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not process profile image upload."
        )
    finally:
        await file.close() # Ensure file handle is closed


@router.put("/password")
async def update_user_password(
    password_data: PasswordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Updates the current authenticated user's password."""
    # 1. Verify current password
    if not auth_service.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password."
        )

    # 2. Hash new password (schema validation already checked match and length)
    hashed_new_password = auth_service.get_password_hash(password_data.new_password)

    # 3. Update password in DB
    current_user.hashed_password = hashed_new_password
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error updating password for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update password."
        )

    # Return simple success message as per requirements
    return {"message": "Password updated successfully."}