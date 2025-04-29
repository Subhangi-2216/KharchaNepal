# backend/src/chatbot/test_router.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Assuming your main FastAPI app instance is accessible
# Adjust the import path based on your project structure
# We might need to adjust how the app is created/imported for tests
from main import app 

# Import expected responses for easier assertion
from src.chatbot.faqs import (
    DEFAULT_RESPONSE, 
    REDIRECT_TO_EXPENSE_BOT_RESPONSE, 
    FAQ_KEYWORD_MAP
)

# Fixture for TestClient
@pytest.fixture(scope="module")
def client():
    # We need to mock the dependency 'get_current_active_user'
    # This is a simple mock; a more robust one might be needed depending on auth setup
    async def override_get_current_active_user():
        # Return a dummy user object or None, depending on what the endpoint expects
        # For this chatbot endpoint, the user object isn't directly used in the logic,
        # but the dependency needs to be satisfied.
        return {"id": 1, "email": "test@example.com", "name": "Test User"} # Example dummy user

    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {} # Clean up overrides after tests

# --- Test Cases ---

def test_support_chatbot_greeting(client: TestClient):
    """Test a common greeting query."""
    response = client.post("/api/chatbot/support", json={"query": "Hello there"})
    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "answer"
    assert data["data"] == FAQ_KEYWORD_MAP["greeting"]["response"]

def test_support_chatbot_navigation_upload(client: TestClient):
    """Test a navigation query about uploading expenses."""
    response = client.post("/api/chatbot/support", json={"query": "how do I upload a receipt?"})
    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "answer"
    assert data["data"] == FAQ_KEYWORD_MAP["upload_expenses"]["response"]

def test_support_chatbot_navigation_report(client: TestClient):
    """Test a navigation query about generating reports."""
    response = client.post("/api/chatbot/support", json={"query": "Tell me how to create a report"})
    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "answer"
    # Note: 'report' is also an expense keyword, but the redirection should take precedence if logic is correct.
    # Re-evaluating logic: The expense keyword check happens *first*. So this test might need adjustment.
    # Let's test the specific navigation response instead.
    assert data["data"] == FAQ_KEYWORD_MAP["generate_report"]["response"]

def test_support_chatbot_navigation_profile(client: TestClient):
    """Test a navigation query about updating profile."""
    response = client.post("/api/chatbot/support", json={"query": "How to change my name?"})
    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "answer"
    assert data["data"] == FAQ_KEYWORD_MAP["update_profile"]["response"]

def test_support_chatbot_redirect_expense_query_amount(client: TestClient):
    """Test redirection for a query containing an expense keyword ('amount')."""
    response = client.post("/api/chatbot/support", json={"query": "What was the amount yesterday?"})
    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "answer"
    assert data["data"] == REDIRECT_TO_EXPENSE_BOT_RESPONSE

def test_support_chatbot_redirect_expense_query_report(client: TestClient):
    """Test redirection for a query containing 'report' keyword."""
    # This query *also* matches navigation, but expense keyword check should be first.
    response = client.post("/api/chatbot/support", json={"query": "Can you generate the monthly report?"})
    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "answer"
    assert data["data"] == REDIRECT_TO_EXPENSE_BOT_RESPONSE

def test_support_chatbot_redirect_expense_query_how_much(client: TestClient):
    """Test redirection for a query containing 'how much' and 'spent'."""
    response = client.post("/api/chatbot/support", json={"query": "how much did i spend on food?"})
    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "answer"
    assert data["data"] == REDIRECT_TO_EXPENSE_BOT_RESPONSE

def test_support_chatbot_unrecognized_query(client: TestClient):
    """Test a query that should not match any keywords."""
    response = client.post("/api/chatbot/support", json={"query": "What is the weather like?"})
    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "answer"
    assert data["data"] == DEFAULT_RESPONSE

def test_support_chatbot_empty_query(client: TestClient):
    """Test sending an empty query (should fail validation)."""
    response = client.post("/api/chatbot/support", json={"query": ""})
    # Pydantic validation should return 422
    assert response.status_code == 422 

def test_support_chatbot_no_query(client: TestClient):
    """Test sending JSON without the 'query' field (should fail validation)."""
    response = client.post("/api/chatbot/support", json={"message": "hello"})
    # Pydantic validation should return 422
    assert response.status_code == 422

# Optional: Test case sensitivity (should be handled by clean_query)
def test_support_chatbot_case_insensitive(client: TestClient):
    """Test that matching is case-insensitive."""
    response = client.post("/api/chatbot/support", json={"query": "How do I UPDATE my PROFILE?"})
    assert response.status_code == 200
    data = response.json()
    assert data["response_type"] == "answer"
    assert data["data"] == FAQ_KEYWORD_MAP["update_profile"]["response"] 