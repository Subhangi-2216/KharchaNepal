"""
Unit tests for email content parsing and extraction.
"""
import pytest
from unittest.mock import Mock, patch

from src.email_processing.email_parser import EmailContentExtractor


class TestEmailContentExtractor:
    """Test email content extraction functionality."""
    
    @pytest.fixture
    def extractor(self):
        """Create email content extractor instance."""
        return EmailContentExtractor()
    
    def test_is_financial_email_bank_sender(self, extractor):
        """Test financial email detection with bank sender."""
        assert extractor.is_financial_email("noreply@chase.bank.com", "Account Statement")
        assert extractor.is_financial_email("alerts@wellsfargo.banking.com", "Transaction Alert")
        assert extractor.is_financial_email("service@bankofamerica.com", "Payment Confirmation")
    
    def test_is_financial_email_payment_processor(self, extractor):
        """Test financial email detection with payment processors."""
        assert extractor.is_financial_email("service@paypal.com", "Payment Received")
        assert extractor.is_financial_email("receipts@stripe.com", "Payment Receipt")
        assert extractor.is_financial_email("noreply@square.com", "Transaction Summary")
    
    def test_is_financial_email_nepali_services(self, extractor):
        """Test financial email detection with Nepali payment services."""
        assert extractor.is_financial_email("noreply@esewa.com.np", "Payment Successful")
        assert extractor.is_financial_email("service@khalti.com", "Transaction Receipt")
        assert extractor.is_financial_email("alerts@ime.com.np", "Money Transfer")
    
    def test_is_financial_email_subject_keywords(self, extractor):
        """Test financial email detection with subject keywords."""
        assert extractor.is_financial_email("any@example.com", "Payment Receipt")
        assert extractor.is_financial_email("any@example.com", "Invoice #12345")
        assert extractor.is_financial_email("any@example.com", "Transaction Confirmation")
        assert extractor.is_financial_email("any@example.com", "Your Bill is Due")
        assert extractor.is_financial_email("any@example.com", "Purchase Confirmation")
    
    def test_is_not_financial_email(self, extractor):
        """Test non-financial email detection."""
        assert not extractor.is_financial_email("newsletter@example.com", "Weekly Newsletter")
        assert not extractor.is_financial_email("support@example.com", "How to use our service")
        assert not extractor.is_financial_email("marketing@example.com", "Special Offer")
    
    def test_extract_transaction_patterns_amounts(self, extractor):
        """Test extracting amount patterns from text."""
        text = """
        Thank you for your payment of Rs. 1,250.50
        Total amount: $99.99
        You paid NPR 500 for this transaction
        Amount: 1000.00
        """
        
        patterns = extractor.extract_transaction_patterns(text)
        
        assert "1,250.50" in patterns["amounts"]
        assert "99.99" in patterns["amounts"]
        assert "500" in patterns["amounts"]
        assert "1000.00" in patterns["amounts"]
    
    def test_extract_transaction_patterns_dates(self, extractor):
        """Test extracting date patterns from text."""
        text = """
        Transaction date: 12/25/2023
        Processed on 2023-12-25
        Date: December 25, 2023
        """
        
        patterns = extractor.extract_transaction_patterns(text)
        
        assert "12/25/2023" in patterns["dates"]
        assert "2023-12-25" in patterns["dates"]
        assert "December 25, 2023" in patterns["dates"]
    
    def test_extract_transaction_patterns_transaction_ids(self, extractor):
        """Test extracting transaction ID patterns from text."""
        text = """
        Transaction ID: TXN123456789
        Reference: REF987654321
        Order #: ORD555666777
        TXN: ABC123XYZ
        """
        
        patterns = extractor.extract_transaction_patterns(text)
        
        assert "TXN123456789" in patterns["transaction_ids"]
        assert "REF987654321" in patterns["transaction_ids"]
        assert "ORD555666777" in patterns["transaction_ids"]
        assert "ABC123XYZ" in patterns["transaction_ids"]
    
    def test_extract_transaction_patterns_merchants(self, extractor):
        """Test extracting merchant patterns from text."""
        text = """
        Payment to Amazon Store
        Transaction at Starbucks Coffee
        Purchase from Best Buy Electronics
        Merchant: Target Corporation
        """
        
        patterns = extractor.extract_transaction_patterns(text)
        
        # Check if any merchant names are extracted
        assert len(patterns["merchants"]) > 0
        # Verify some expected merchants are found
        merchant_text = " ".join(patterns["merchants"]).lower()
        assert any(name in merchant_text for name in ["amazon", "starbucks", "target"])
    
    def test_extract_transaction_patterns_empty_text(self, extractor):
        """Test extracting patterns from empty text."""
        patterns = extractor.extract_transaction_patterns("")
        
        assert patterns["amounts"] == []
        assert patterns["dates"] == []
        assert patterns["merchants"] == []
        assert patterns["transaction_ids"] == []
    
    def test_extract_transaction_patterns_no_matches(self, extractor):
        """Test extracting patterns from text with no financial patterns."""
        text = "This is just a regular email with no financial information."
        
        patterns = extractor.extract_transaction_patterns(text)
        
        assert patterns["amounts"] == []
        assert patterns["dates"] == []
        assert patterns["merchants"] == []
        assert patterns["transaction_ids"] == []
    
    @patch('src.email_processing.email_parser.build')
    @patch('src.email_processing.email_parser.Credentials')
    def test_extract_gmail_message_content_basic(self, mock_credentials, mock_build, extractor):
        """Test basic Gmail message content extraction."""
        # Mock Gmail API response
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        mock_message = {
            "id": "test_message_id",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Payment Receipt"},
                    {"name": "From", "value": "bank@example.com"},
                    {"name": "Date", "value": "Mon, 25 Dec 2023 10:00:00 +0000"}
                ],
                "mimeType": "text/plain",
                "body": {
                    "data": "VGhhbmsgeW91IGZvciB5b3VyIHBheW1lbnQ="  # Base64 for "Thank you for your payment"
                }
            }
        }
        
        mock_service.users().messages().get().execute.return_value = mock_message
        
        result = extractor.extract_gmail_message_content("test_token", "test_message_id")
        
        assert result["message_id"] == "test_message_id"
        assert result["subject"] == "Payment Receipt"
        assert result["sender"] == "bank@example.com"
        assert result["is_financial"] is True
        assert "Thank you for your payment" in result["body_text"]
