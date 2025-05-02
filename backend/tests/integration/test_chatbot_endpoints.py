# backend/tests/integration/test_chatbot_endpoints.py
"""
Integration tests for the chatbot endpoints.
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from main import app
from database import get_db
from models import User, Expense, CategoryEnum
from src.auth.dependencies import get_current_active_user

# --- Fixtures ---

@pytest.fixture
def mock_user():
    """Mock user for testing."""
    return User(
        id=1,
        name="Test User",
        email="test@example.com",
        hashed_password="hashed_password"
    )

@pytest.fixture
def mock_expenses():
    """Mock expenses for testing."""
    return [
        Expense(
            id=1,
            user_id=1,
            merchant_name="Restaurant ABC",
            date="2023-01-01",
            amount=500.00,
            currency="NPR",
            category=CategoryEnum.FOOD,
            is_ocr_entry=False
        ),
        Expense(
            id=2,
            user_id=1,
            merchant_name="Taxi Service",
            date="2023-01-02",
            amount=300.00,
            currency="NPR",
            category=CategoryEnum.TRAVEL,
            is_ocr_entry=False
        ),
        Expense(
            id=3,
            user_id=1,
            merchant_name="Movie Theater",
            date="2023-01-03",
            amount=400.00,
            currency="NPR",
            category=CategoryEnum.ENTERTAINMENT,
            is_ocr_entry=False
        )
    ]

@pytest.fixture
async def mock_db(mock_user, mock_expenses):
    """Mock database session for testing."""
    # This would be implemented with a test database or mocks
    pass

@pytest.fixture
def override_get_current_user():
    """Override the get_current_active_user dependency."""
    async def mock_get_current_active_user():
        return User(
            id=1,
            name="Test User",
            email="test@example.com",
            hashed_password="hashed_password"
        )
    
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    yield
    app.dependency_overrides.pop(get_current_active_user)

@pytest.fixture
def override_get_db():
    """Override the get_db dependency."""
    async def mock_get_db():
        # This would be implemented with a test database or mocks
        yield None
    
    app.dependency_overrides[get_db] = mock_get_db
    yield
    app.dependency_overrides.pop(get_db)

# --- Tests ---

@pytest.mark.asyncio
async def test_support_chatbot_endpoint(override_get_current_user, override_get_db):
    """Test the support chatbot endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/chatbot/support",
            json={"query": "How do I add an expense?"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "response_type" in response.json()
        assert "data" in response.json()
        assert response.json()["response_type"] == "answer"
        assert "expense" in response.json()["data"].lower()

@pytest.mark.asyncio
async def test_expense_chatbot_query_sum(override_get_current_user, override_get_db):
    """Test the expense chatbot query sum endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/chatbot/query",
            json={"query": "How much did I spend on food last month?"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "response_type" in response.json()
        assert "data" in response.json()
        # Note: Actual data validation would depend on the mock database implementation

@pytest.mark.asyncio
async def test_expense_chatbot_query_list(override_get_current_user, override_get_db):
    """Test the expense chatbot query list endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/chatbot/query",
            json={"query": "Show me my travel expenses this week"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "response_type" in response.json()
        assert "data" in response.json()
        # Note: Actual data validation would depend on the mock database implementation

@pytest.mark.asyncio
async def test_expense_chatbot_add_expense(override_get_current_user, override_get_db):
    """Test the expense chatbot add expense endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/chatbot/query",
            json={"query": "Add a new expense of Rs 500 for food at Restaurant ABC yesterday"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "response_type" in response.json()
        assert "data" in response.json()
        # Note: Actual data validation would depend on the mock database implementation

@pytest.mark.asyncio
async def test_expense_chatbot_unknown_query(override_get_current_user, override_get_db):
    """Test the expense chatbot with an unknown query."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/chatbot/query",
            json={"query": "What is the meaning of life?"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "response_type" in response.json()
        assert "data" in response.json()
        assert response.json()["response_type"] == "error"
        assert "not sure" in response.json()["data"].lower()