"""
Simplified integration tests for email processing functionality.
"""
import pytest
from unittest.mock import patch, Mock

from src.email_processing.gmail_service import GmailService
from src.email_processing.email_parser import EmailContentExtractor
from src.email_processing.encryption import CredentialEncryption


class TestGmailServiceIntegration:
    """Test Gmail service integration without authentication."""
    
    def test_gmail_service_initialization(self):
        """Test Gmail service can be initialized."""
        service = GmailService()
        assert service is not None
        assert hasattr(service, 'get_authorization_url')
        assert hasattr(service, 'exchange_code_for_tokens')
    
    @patch('src.email_processing.gmail_service.settings')
    def test_authorization_url_generation(self, mock_settings):
        """Test OAuth authorization URL generation."""
        mock_settings.GMAIL_CLIENT_ID = "test_client_id"
        mock_settings.GMAIL_CLIENT_SECRET = "test_client_secret"
        mock_settings.GMAIL_REDIRECT_URI = "http://localhost:8000/callback"
        
        service = GmailService()
        url = service.get_authorization_url("test_state")
        
        assert "accounts.google.com" in url
        assert "test_client_id" in url
        assert "state=test_state" in url
    
    @patch('src.email_processing.gmail_service.Flow')
    def test_token_exchange(self, mock_flow_class):
        """Test OAuth token exchange."""
        # Mock the Flow class and its methods
        mock_flow = Mock()
        mock_flow_class.from_client_config.return_value = mock_flow
        
        mock_credentials = Mock()
        mock_credentials.token = "test_access_token"
        mock_credentials.refresh_token = "test_refresh_token"
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.client_id = "test_client_id"
        mock_credentials.client_secret = "test_client_secret"
        mock_credentials.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        mock_credentials.expiry = None
        
        mock_flow.credentials = mock_credentials
        
        service = GmailService()
        result = service.exchange_code_for_tokens("test_authorization_code")
        
        assert result["access_token"] == "test_access_token"
        assert result["refresh_token"] == "test_refresh_token"
        assert "gmail.readonly" in str(result["scopes"])


class TestEmailContentExtractorIntegration:
    """Test email content extractor integration."""
    
    def test_extractor_initialization(self):
        """Test email content extractor can be initialized."""
        extractor = EmailContentExtractor()
        assert extractor is not None
        assert hasattr(extractor, 'is_financial_email')
        assert hasattr(extractor, 'extract_transaction_patterns')
    
    def test_financial_email_detection_comprehensive(self):
        """Test comprehensive financial email detection."""
        extractor = EmailContentExtractor()
        
        # Test various financial email patterns
        test_cases = [
            ("noreply@chase.bank.com", "Account Statement", True),
            ("service@paypal.com", "Payment Received", True),
            ("alerts@esewa.com.np", "Payment Successful", True),
            ("any@example.com", "Payment Receipt", True),
            ("newsletter@example.com", "Weekly Newsletter", False),
            ("support@example.com", "How to use our service", False),
        ]
        
        for sender, subject, expected in test_cases:
            result = extractor.is_financial_email(sender, subject)
            assert result == expected, f"Failed for {sender}, {subject}"
    
    def test_transaction_pattern_extraction_comprehensive(self):
        """Test comprehensive transaction pattern extraction."""
        extractor = EmailContentExtractor()
        
        test_email_content = """
        Dear Customer,
        
        Thank you for your payment of Rs. 1,250.50 on 12/25/2023.
        Transaction ID: TXN123456789
        Reference: REF987654321
        Merchant: Amazon Store
        Total amount: $99.99
        
        Order #: ORD555666777
        Date: December 25, 2023
        You paid NPR 500 for this transaction at Starbucks Coffee.
        
        Best regards,
        Payment Team
        """
        
        patterns = extractor.extract_transaction_patterns(test_email_content)
        
        # Check amounts
        assert "1,250.50" in patterns["amounts"]
        assert "99.99" in patterns["amounts"]
        assert "500" in patterns["amounts"]
        
        # Check dates
        assert "12/25/2023" in patterns["dates"]
        assert "December 25, 2023" in patterns["dates"]
        
        # Check transaction IDs
        assert "TXN123456789" in patterns["transaction_ids"]
        assert "REF987654321" in patterns["transaction_ids"]
        assert "ORD555666777" in patterns["transaction_ids"]
        
        # Check merchants (at least some should be found)
        assert len(patterns["merchants"]) > 0


class TestCredentialEncryptionIntegration:
    """Test credential encryption integration."""
    
    @patch('src.email_processing.encryption.settings')
    def test_encryption_decryption_cycle(self, mock_settings):
        """Test complete encryption/decryption cycle."""
        # Use a valid Fernet key
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key().decode()
        mock_settings.ENCRYPTION_KEY = test_key
        
        encryption = CredentialEncryption()
        
        test_credentials = {
            "access_token": "test_access_token_12345",
            "refresh_token": "test_refresh_token_67890",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
            "user_info": {
                "email": "test@gmail.com",
                "verified": True
            }
        }
        
        # Encrypt
        encrypted = encryption.encrypt_credentials(test_credentials)
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
        assert encrypted != str(test_credentials)
        
        # Decrypt
        decrypted = encryption.decrypt_credentials(encrypted)
        assert decrypted == test_credentials
        assert decrypted["access_token"] == "test_access_token_12345"
        assert decrypted["user_info"]["email"] == "test@gmail.com"


class TestEmailProcessingWorkflow:
    """Test the complete email processing workflow."""
    
    @patch('src.email_processing.gmail_service.settings')
    def test_oauth_workflow_simulation(self, mock_settings):
        """Test simulated OAuth workflow."""
        mock_settings.GMAIL_CLIENT_ID = "test_client_id"
        mock_settings.GMAIL_CLIENT_SECRET = "test_client_secret"
        mock_settings.GMAIL_REDIRECT_URI = "http://localhost:8000/callback"
        
        service = GmailService()
        
        # Step 1: Generate authorization URL
        auth_url = service.get_authorization_url("user_123")
        assert "accounts.google.com" in auth_url
        assert "state=user_123" in auth_url
        
        # Step 2: Simulate token exchange (mocked)
        with patch('src.email_processing.gmail_service.Flow') as mock_flow_class:
            mock_flow = Mock()
            mock_flow_class.from_client_config.return_value = mock_flow
            
            mock_credentials = Mock()
            mock_credentials.token = "access_token_123"
            mock_credentials.refresh_token = "refresh_token_456"
            mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
            mock_credentials.client_id = "test_client_id"
            mock_credentials.client_secret = "test_client_secret"
            mock_credentials.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
            mock_credentials.expiry = None
            
            mock_flow.credentials = mock_credentials
            
            tokens = service.exchange_code_for_tokens("auth_code_789")
            assert tokens["access_token"] == "access_token_123"
            assert tokens["refresh_token"] == "refresh_token_456"
    
    def test_email_processing_pipeline(self):
        """Test the email processing pipeline."""
        extractor = EmailContentExtractor()
        
        # Simulate processing a financial email
        sender = "noreply@bank.com"
        subject = "Payment Confirmation"
        email_body = """
        Dear Customer,
        Your payment of Rs. 2,500.00 has been processed.
        Transaction ID: TXN987654321
        Date: 2023-12-25
        Merchant: Online Store
        """
        
        # Step 1: Detect if email is financial
        is_financial = extractor.is_financial_email(sender, subject)
        assert is_financial is True
        
        # Step 2: Extract transaction patterns
        patterns = extractor.extract_transaction_patterns(email_body)
        
        # Verify extraction results
        assert "2,500.00" in patterns["amounts"]
        assert "TXN987654321" in patterns["transaction_ids"]
        assert "2023-12-25" in patterns["dates"]
        
        # Step 3: Simulate creating approval record
        approval_data = {
            "extracted_data": patterns,
            "confidence_score": 0.85,
            "source": "email_text"
        }
        
        assert approval_data["confidence_score"] > 0.8
        assert "amounts" in approval_data["extracted_data"]
        assert len(approval_data["extracted_data"]["amounts"]) > 0


class TestSystemIntegration:
    """Test system-level integration."""
    
    def test_all_services_can_be_imported(self):
        """Test that all email processing services can be imported."""
        from src.email_processing.gmail_service import gmail_service
        from src.email_processing.email_parser import email_extractor
        from src.email_processing.encryption import credential_encryption
        
        assert gmail_service is not None
        assert email_extractor is not None
        assert credential_encryption is not None
    
    def test_celery_tasks_can_be_imported(self):
        """Test that Celery tasks can be imported."""
        from src.email_processing.tasks import (
            sync_gmail_messages,
            process_email,
            extract_transaction_data
        )
        
        assert sync_gmail_messages is not None
        assert process_email is not None
        assert extract_transaction_data is not None
    
    def test_models_can_be_imported(self):
        """Test that email processing models can be imported."""
        from models import EmailAccount, EmailMessage, TransactionApproval
        
        assert EmailAccount is not None
        assert EmailMessage is not None
        assert TransactionApproval is not None
