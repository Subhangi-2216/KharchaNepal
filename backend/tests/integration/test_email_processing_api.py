"""
Integration tests for email processing API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db
from models import User, EmailAccount
from src.auth.service import create_access_token


@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def client(db_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        name="Test User",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers."""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


class TestEmailOAuthEndpoints:
    """Test OAuth-related endpoints."""
    
    @patch('src.email_processing.router.gmail_service')
    def test_initiate_oauth(self, mock_gmail_service, client, auth_headers):
        """Test initiating Gmail OAuth flow."""
        mock_gmail_service.get_authorization_url.return_value = "https://accounts.google.com/oauth/authorize?..."
        
        response = client.get("/api/email/oauth/authorize", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert data["authorization_url"].startswith("https://accounts.google.com")
        assert "message" in data
    
    @patch('src.email_processing.router.gmail_service')
    def test_oauth_callback_success(self, mock_gmail_service, client, db_session):
        """Test successful OAuth callback."""
        # Mock Gmail service methods
        mock_gmail_service.exchange_code_for_tokens.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token"
        }
        mock_gmail_service.get_user_email.return_value = "user@gmail.com"
        mock_gmail_service.save_email_account.return_value = Mock(id=1)
        
        response = client.get(
            "/api/email/oauth/callback",
            params={"code": "test_code", "state": "1"}
        )
        
        assert response.status_code == 302  # Redirect
        assert "oauth_success=true" in response.headers["location"]
    
    def test_oauth_callback_error(self, client):
        """Test OAuth callback with error."""
        response = client.get(
            "/api/email/oauth/callback",
            params={"error": "access_denied", "state": "1"}
        )
        
        assert response.status_code == 302  # Redirect
        assert "oauth_error=access_denied" in response.headers["location"]


class TestEmailAccountEndpoints:
    """Test email account management endpoints."""
    
    def test_list_email_accounts_empty(self, client, auth_headers):
        """Test listing email accounts when none exist."""
        response = client.get("/api/email/accounts", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_email_accounts_with_data(self, client, auth_headers, test_user, db_session):
        """Test listing email accounts with existing data."""
        # Create test email account
        account = EmailAccount(
            user_id=test_user.id,
            email_address="test@gmail.com",
            oauth_credentials="encrypted_credentials",
            is_active=True
        )
        db_session.add(account)
        db_session.commit()
        
        response = client.get("/api/email/accounts", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email_address"] == "test@gmail.com"
        assert data[0]["is_active"] is True
    
    @patch('src.email_processing.router.gmail_service')
    def test_sync_email_account_success(self, mock_gmail_service, client, auth_headers, test_user, db_session):
        """Test successful email account sync."""
        # Create test email account
        account = EmailAccount(
            user_id=test_user.id,
            email_address="test@gmail.com",
            oauth_credentials="encrypted_credentials",
            is_active=True
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)
        
        # Mock sync response
        mock_gmail_service.sync_messages_for_account.return_value = [
            {
                "message_id": "msg1",
                "subject": "Payment Receipt",
                "sender": "bank@example.com",
                "received_at": "2023-12-25T10:00:00",
                "has_attachments": False
            }
        ]
        
        response = client.post(f"/api/email/accounts/{account.id}/sync", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["account_id"] == account.id
        assert data["synced_messages"] == 1
        assert len(data["messages"]) == 1
    
    def test_sync_nonexistent_account(self, client, auth_headers):
        """Test syncing non-existent email account."""
        response = client.post("/api/email/accounts/999/sync", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_disconnect_email_account(self, client, auth_headers, test_user, db_session):
        """Test disconnecting an email account."""
        # Create test email account
        account = EmailAccount(
            user_id=test_user.id,
            email_address="test@gmail.com",
            oauth_credentials="encrypted_credentials",
            is_active=True
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)
        
        response = client.delete(f"/api/email/accounts/{account.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "disconnected successfully" in data["message"]
        
        # Verify account is marked as inactive
        db_session.refresh(account)
        assert account.is_active is False
    
    def test_disconnect_nonexistent_account(self, client, auth_headers):
        """Test disconnecting non-existent email account."""
        response = client.delete("/api/email/accounts/999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestAuthenticationRequired:
    """Test that authentication is required for all endpoints."""
    
    def test_oauth_authorize_requires_auth(self, client):
        """Test that OAuth authorize requires authentication."""
        response = client.get("/api/email/oauth/authorize")
        assert response.status_code == 401
    
    def test_list_accounts_requires_auth(self, client):
        """Test that listing accounts requires authentication."""
        response = client.get("/api/email/accounts")
        assert response.status_code == 401
    
    def test_sync_account_requires_auth(self, client):
        """Test that syncing account requires authentication."""
        response = client.post("/api/email/accounts/1/sync")
        assert response.status_code == 401
    
    def test_disconnect_account_requires_auth(self, client):
        """Test that disconnecting account requires authentication."""
        response = client.delete("/api/email/accounts/1")
        assert response.status_code == 401
