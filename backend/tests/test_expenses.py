import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from datetime import date

from auth.service import get_password_hash # To create user
from models import User as UserModel # To create user

# Helper fixture to create a test user and get an auth token
@pytest.fixture(scope="module")
async def test_user_token(client: AsyncClient, db_session: AsyncSession):
    # Create user directly in DB for simplicity
    user_email = "test_expense_user@example.com"
    hashed_password = get_password_hash("password123")
    test_user = UserModel(email=user_email, name="Test Expense User", hashed_password=hashed_password)
    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)

    # Login to get token
    login_data = {"username": user_email, "password": "password123"}
    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers

# --- Tests for POST /api/expenses/manual --- 

@pytest.mark.asyncio
async def test_create_manual_expense_success(client: AsyncClient, test_user_token: dict):
    expense_data = {
        "merchant_name": "Test Merchant",
        "date": date.today().isoformat(), # Use today's date
        "amount": 123.45,
        "category": "Food" # Valid category
    }
    response = await client.post("/api/expenses/manual", json=expense_data, headers=test_user_token)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["merchant_name"] == expense_data["merchant_name"]
    assert data["amount"] == expense_data["amount"]
    assert data["category"] == expense_data["category"]
    assert data["currency"] == "NPR"
    assert data["is_ocr_entry"] == False
    assert "id" in data

@pytest.mark.asyncio
async def test_create_manual_expense_invalid_category(client: AsyncClient, test_user_token: dict):
    expense_data = {
        "merchant_name": "Test Invalid Cat",
        "date": date.today().isoformat(),
        "amount": 50.00,
        "category": "INVALID_CATEGORY" # Invalid category
    }
    response = await client.post("/api/expenses/manual", json=expense_data, headers=test_user_token)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # Pydantic validation error

@pytest.mark.asyncio
async def test_create_manual_expense_missing_field(client: AsyncClient, test_user_token: dict):
    expense_data = { # Missing merchant_name
        "date": date.today().isoformat(),
        "amount": 50.00,
        "category": "Travel"
    }
    response = await client.post("/api/expenses/manual", json=expense_data, headers=test_user_token)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_create_manual_expense_invalid_amount(client: AsyncClient, test_user_token: dict):
    expense_data = {
        "merchant_name": "Test Invalid Amount",
        "date": date.today().isoformat(),
        "amount": -10.00, # Invalid amount
        "category": "Travel"
    }
    response = await client.post("/api/expenses/manual", json=expense_data, headers=test_user_token)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_create_manual_expense_unauthorized(client: AsyncClient):
    expense_data = {
        "merchant_name": "Unauthorized Merchant",
        "date": date.today().isoformat(),
        "amount": 10.00,
        "category": "Food"
    }
    response = await client.post("/api/expenses/manual", json=expense_data) # No headers
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# --- Tests for GET /api/expenses --- 

@pytest.mark.asyncio
async def test_read_expenses_success(client: AsyncClient, test_user_token: dict):
    # First, add an expense to make sure there's something to retrieve
    expense_data = {
        "merchant_name": "Merchant For Get",
        "date": date.today().isoformat(), 
        "amount": 99.99,
        "category": "Entertainment"
    }
    post_response = await client.post("/api/expenses/manual", json=expense_data, headers=test_user_token)
    assert post_response.status_code == status.HTTP_201_CREATED
    posted_data = post_response.json()

    # Now, try to get expenses
    response = await client.get("/api/expenses", headers=test_user_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Check if the newly added expense is in the list
    assert any(item["id"] == posted_data["id"] for item in data)
    assert any(item["merchant_name"] == "Merchant For Get" for item in data)

@pytest.mark.asyncio
async def test_read_expenses_unauthorized(client: AsyncClient):
    response = await client.get("/api/expenses") # No headers
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 