"""
Unit tests for email processing database models.
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from models import (
    User, EmailAccount, EmailMessage, TransactionApproval,
    ProcessingStatusEnum, ApprovalStatusEnum
)


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        name="Test User",
        email="test@example.com",
        hashed_password="hashed_password_here"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestEmailAccount:
    """Test EmailAccount model."""
    
    def test_create_email_account(self, db_session, test_user):
        """Test creating an email account."""
        account = EmailAccount(
            user_id=test_user.id,
            email_address="test@gmail.com",
            oauth_credentials="encrypted_credentials",
            is_active=True
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)
        
        assert account.id is not None
        assert account.user_id == test_user.id
        assert account.email_address == "test@gmail.com"
        assert account.is_active is True
        assert account.created_at is not None
        assert account.updated_at is not None
    
    def test_email_account_relationships(self, db_session, test_user):
        """Test EmailAccount relationships."""
        account = EmailAccount(
            user_id=test_user.id,
            email_address="test@gmail.com",
            oauth_credentials="encrypted_credentials"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)
        
        # Test user relationship
        assert account.user.id == test_user.id
        assert account.user.email == "test@example.com"
        
        # Test reverse relationship
        assert len(test_user.email_accounts) == 1
        assert test_user.email_accounts[0].id == account.id


class TestEmailMessage:
    """Test EmailMessage model."""
    
    def test_create_email_message(self, db_session, test_user):
        """Test creating an email message."""
        # Create email account first
        account = EmailAccount(
            user_id=test_user.id,
            email_address="test@gmail.com",
            oauth_credentials="encrypted_credentials"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)
        
        # Create email message
        message = EmailMessage(
            email_account_id=account.id,
            message_id="gmail_message_123",
            subject="Payment Receipt",
            sender="bank@example.com",
            received_at=datetime.utcnow(),
            has_attachments=True,
            processing_status=ProcessingStatusEnum.PENDING
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        assert message.id is not None
        assert message.email_account_id == account.id
        assert message.message_id == "gmail_message_123"
        assert message.subject == "Payment Receipt"
        assert message.sender == "bank@example.com"
        assert message.has_attachments is True
        assert message.processing_status == ProcessingStatusEnum.PENDING
    
    def test_email_message_relationships(self, db_session, test_user):
        """Test EmailMessage relationships."""
        # Create email account
        account = EmailAccount(
            user_id=test_user.id,
            email_address="test@gmail.com",
            oauth_credentials="encrypted_credentials"
        )
        db_session.add(account)
        db_session.commit()
        
        # Create email message
        message = EmailMessage(
            email_account_id=account.id,
            message_id="gmail_message_123",
            subject="Test",
            sender="test@example.com",
            received_at=datetime.utcnow()
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        # Test email account relationship
        assert message.email_account.id == account.id
        assert message.email_account.email_address == "test@gmail.com"
        
        # Test reverse relationship
        assert len(account.email_messages) == 1
        assert account.email_messages[0].id == message.id


class TestTransactionApproval:
    """Test TransactionApproval model."""
    
    def test_create_transaction_approval(self, db_session, test_user):
        """Test creating a transaction approval."""
        # Create email account and message
        account = EmailAccount(
            user_id=test_user.id,
            email_address="test@gmail.com",
            oauth_credentials="encrypted_credentials"
        )
        db_session.add(account)
        db_session.commit()
        
        message = EmailMessage(
            email_account_id=account.id,
            message_id="gmail_message_123",
            subject="Payment Receipt",
            sender="bank@example.com",
            received_at=datetime.utcnow()
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        # Create transaction approval
        approval = TransactionApproval(
            user_id=test_user.id,
            email_message_id=message.id,
            extracted_data={"amount": "100.00", "merchant": "Test Store"},
            confidence_score=0.85,
            approval_status=ApprovalStatusEnum.PENDING
        )
        db_session.add(approval)
        db_session.commit()
        db_session.refresh(approval)
        
        assert approval.id is not None
        assert approval.user_id == test_user.id
        assert approval.email_message_id == message.id
        assert approval.extracted_data["amount"] == "100.00"
        assert float(approval.confidence_score) == 0.85
        assert approval.approval_status == ApprovalStatusEnum.PENDING
    
    def test_transaction_approval_relationships(self, db_session, test_user):
        """Test TransactionApproval relationships."""
        # Create email account and message
        account = EmailAccount(
            user_id=test_user.id,
            email_address="test@gmail.com",
            oauth_credentials="encrypted_credentials"
        )
        db_session.add(account)
        db_session.commit()
        
        message = EmailMessage(
            email_account_id=account.id,
            message_id="gmail_message_123",
            subject="Test",
            sender="test@example.com",
            received_at=datetime.utcnow()
        )
        db_session.add(message)
        db_session.commit()
        
        # Create transaction approval
        approval = TransactionApproval(
            user_id=test_user.id,
            email_message_id=message.id,
            extracted_data={"test": "data"},
            approval_status=ApprovalStatusEnum.PENDING
        )
        db_session.add(approval)
        db_session.commit()
        db_session.refresh(approval)
        
        # Test relationships
        assert approval.user.id == test_user.id
        assert approval.email_message.id == message.id
        
        # Test reverse relationships
        assert len(test_user.transaction_approvals) == 1
        assert test_user.transaction_approvals[0].id == approval.id
        
        assert len(message.transaction_approvals) == 1
        assert message.transaction_approvals[0].id == approval.id
