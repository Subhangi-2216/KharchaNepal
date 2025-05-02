"""
Integration tests for OCR endpoint.
"""

import pytest
import os
import sys
from pathlib import Path
from io import BytesIO
from decimal import Decimal
import asyncio
from httpx import AsyncClient

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from database import get_db, engine
from models import Base, User
from src.auth.service import get_password_hash

# Test user credentials
TEST_USER = {
    "email": "test@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User"
}

# Sample image for testing
SAMPLE_IMAGE_PATH = Path(__file__).parent / "test_data" / "test_receipt.jpg"


@pytest.fixture(scope="module")
async def setup_database():
    """Set up test database and create test user."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create test user
    async with get_db() as db:
        hashed_password = get_password_hash(TEST_USER["password"])
        test_user = User(
            email=TEST_USER["email"],
            hashed_password=hashed_password,
            full_name=TEST_USER["full_name"],
            is_active=True
        )
        db.add(test_user)
        await db.commit()
        await db.refresh(test_user)
        yield test_user

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="module")
async def auth_client(setup_database):
    """Create an authenticated client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Login to get access token
        response = await client.post(
            "/api/auth/token",
            data={
                "username": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
        )
        token = response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
        yield client


@pytest.mark.asyncio
async def test_ocr_endpoint_valid_image(auth_client):
    """Test OCR endpoint with a valid image."""
    # Skip if test image doesn't exist
    if not SAMPLE_IMAGE_PATH.exists():
        pytest.skip(f"Test image not found at {SAMPLE_IMAGE_PATH}")

    # Read test image
    with open(SAMPLE_IMAGE_PATH, "rb") as f:
        image_data = f.read()

    # Create file-like object for upload
    image_file = BytesIO(image_data)
    image_file.name = "test_receipt.jpg"

    # Send request
    files = {"file": (image_file.name, image_file, "image/jpeg")}
    response = await auth_client.post("/api/expenses/ocr", files=files)

    # Check response
    if response.status_code == 201:
        # Success case
        data = response.json()
        assert "expense_id" in data
        assert "extracted_data" in data
        assert "missing_fields" in data
        assert "message" in data

        # Check extracted data
        extracted = data["extracted_data"]
        assert "amount" in extracted
        assert extracted["amount"] is not None

    elif response.status_code == 400:
        # Case where OCR couldn't extract amount
        data = response.json()
        assert "detail" in data
        if isinstance(data["detail"], dict):
            assert "extracted_data" in data["detail"]
            assert "missing_fields" in data["detail"]
            assert "amount" in data["detail"]["missing_fields"]
    else:
        # Unexpected status code
        assert False, f"Unexpected status code: {response.status_code}, response: {response.text}"


@pytest.mark.asyncio
async def test_ocr_endpoint_invalid_file_type(auth_client):
    """Test OCR endpoint with an invalid file type."""
    # Create a text file
    text_file = BytesIO(b"This is not an image")
    text_file.name = "not_an_image.txt"

    # Send request
    files = {"file": (text_file.name, text_file, "text/plain")}
    response = await auth_client.post("/api/expenses/ocr", files=files)

    # Check response
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]
